import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, Body, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.auth import get_current_user
from app.core.errors import NotFoundException, ValidationException, UnsupportedInputException
from app.db.session import get_db
from app.db.models import (
    User,
    Project,
    Asset,
    Snapshot,
    Inventory,
    PackageIdentity,
    Occurrence,
    Edge,
    SnapshotAsset,
)
from app.api.v1.projects import get_user_project
from app.schemas.snapshot import SnapshotRead, GraphResponse, GraphNode, GraphEdge
from app.schemas.common import PaginatedResponse
from app.ingestion.cyclonedx import CycloneDXParser

router = APIRouter(tags=["Snapshots"])


def get_user_snapshot(snapshot_id: uuid.UUID, user: User, db: Session) -> Snapshot:
    """Retrieve snapshot by ID, ensuring user owns the parent project. Fails closed with 404."""
    snapshot = (
        db.query(Snapshot)
        .join(Project, Snapshot.project_id == Project.id)
        .filter(Snapshot.id == snapshot_id, Project.owner_user_id == user.id)
        .first()
    )
    if not snapshot:
        raise NotFoundException(message=f"Snapshot '{snapshot_id}' not found.")
    return snapshot


@router.post("/projects/{project_id}/snapshots", response_model=SnapshotRead, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    project_id: uuid.UUID,
    request: Request,
    asset_id: Optional[uuid.UUID] = Query(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload CycloneDX 1.5/1.6 JSON inventory and atomically create snapshot."""
    project = get_user_project(project_id, current_user, db)

    # Determine associated asset
    target_asset = None
    if asset_id:
        target_asset = db.query(Asset).filter(Asset.id == asset_id, Asset.project_id == project.id).first()
        if not target_asset:
            raise NotFoundException(message=f"Asset '{asset_id}' not found for this project.")
    else:
        # Default to first project asset or create one
        target_asset = db.query(Asset).filter(Asset.project_id == project.id).order_by(Asset.created_at.asc()).first()
        if not target_asset:
            target_asset = Asset(
                project_id=project.id,
                name=f"{project.name} Core",
                environment="production",
                default_weight=3,
            )
            db.add(target_asset)
            db.flush()

    # Read payload from multipart file or raw JSON body
    raw_bytes = b""
    if file:
        raw_bytes = await file.read()
    else:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            raw_bytes = await request.body()
        else:
            raise UnsupportedInputException("Expected CycloneDX file upload (multipart/form-data) or application/json body.")

    if not raw_bytes:
        raise UnsupportedInputException("Empty inventory payload received.")

    # Parse CycloneDX
    parsed = CycloneDXParser.parse_raw(raw_bytes, strict_dangling=False)

    # Atomically persist in DB
    try:
        snapshot = Snapshot(
            project_id=project.id,
            content_hash=parsed.content_hash,
            parser_version=parsed.parser_version,
            topology_status=parsed.topology_status,
            warnings=parsed.warnings,
        )
        db.add(snapshot)
        db.flush()

        inventory = Inventory(
            snapshot_id=snapshot.id,
            asset_id=target_asset.id,
            source_type="cyclonedx-json",
            source_ref=file.filename if file else "direct-upload.json",
            source_hash=parsed.content_hash,
            raw_content=parsed.raw_content,
            warnings=parsed.warnings,
        )
        db.add(inventory)
        db.flush()

        # Snapshot Asset mapping
        root_ref = parsed.root_ref or (parsed.components[0].bom_ref if parsed.components else target_asset.name)
        snap_asset = SnapshotAsset(
            snapshot_id=snapshot.id,
            asset_id=target_asset.id,
            root_ref=root_ref,
            captured_weight=target_asset.default_weight,
            environment_context={"environment": target_asset.environment, "asset_name": target_asset.name},
        )
        db.add(snap_asset)

        # Upsert Package Identities and Occurrences
        # Group components by identity key: (ecosystem, namespace, name, version)
        pkg_identities_cache: Dict[tuple, uuid.UUID] = {}

        for comp in parsed.components:
            key = (comp.ecosystem, comp.namespace or "", comp.name, comp.version)
            pkg_id = pkg_identities_cache.get(key)

            if not pkg_id:
                existing_pkg = (
                    db.query(PackageIdentity)
                    .filter(
                        PackageIdentity.ecosystem == comp.ecosystem,
                        PackageIdentity.namespace == comp.namespace,
                        PackageIdentity.name == comp.name,
                        PackageIdentity.version == comp.version,
                    )
                    .first()
                )
                if existing_pkg:
                    pkg_id = existing_pkg.id
                else:
                    new_pkg = PackageIdentity(
                        ecosystem=comp.ecosystem,
                        namespace=comp.namespace,
                        name=comp.name,
                        version=comp.version,
                        canonical_purl=comp.canonical_purl,
                    )
                    db.add(new_pkg)
                    db.flush()
                    pkg_id = new_pkg.id
                pkg_identities_cache[key] = pkg_id

            occurrence = Occurrence(
                snapshot_id=snapshot.id,
                inventory_id=inventory.id,
                package_identity_id=pkg_id,
                local_ref=comp.bom_ref,
                metadata_json={
                    "name": comp.name,
                    "version": comp.version,
                    "ecosystem": comp.ecosystem,
                    "canonical_purl": comp.canonical_purl,
                    "component_type": comp.component_type,
                    "description": comp.description,
                    "hashes": comp.hashes,
                },
            )
            db.add(occurrence)

        # Persist Edges
        for edge in parsed.edges:
            db_edge = Edge(
                snapshot_id=snapshot.id,
                from_ref=edge.from_ref,
                to_ref=edge.to_ref,
                context=edge.context,
                gate_default=edge.gate_default,
                provenance=edge.provenance,
            )
            db.add(db_edge)

        db.commit()
        db.refresh(snapshot)

        occ_count = len(parsed.components)
        edge_count = len(parsed.edges)

        return SnapshotRead(
            id=snapshot.id,
            project_id=snapshot.project_id,
            content_hash=snapshot.content_hash,
            parser_version=snapshot.parser_version,
            topology_status=snapshot.topology_status,
            warnings=snapshot.warnings,
            created_at=snapshot.created_at,
            occurrence_count=occ_count,
            edge_count=edge_count,
            inventory_count=1,
        )
    except Exception as e:
        db.rollback()
        raise e


@router.get("/projects/{project_id}/snapshots", response_model=PaginatedResponse[SnapshotRead])
def list_project_snapshots(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List snapshots for an owned project."""
    project = get_user_project(project_id, current_user, db)
    query = db.query(Snapshot).filter(Snapshot.project_id == project.id)
    total = query.count()
    offset = (page - 1) * page_size
    snapshots = query.order_by(Snapshot.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for s in snapshots:
        occ_count = db.query(func.count(Occurrence.id)).filter(Occurrence.snapshot_id == s.id).scalar() or 0
        edge_count = db.query(func.count(Edge.id)).filter(Edge.snapshot_id == s.id).scalar() or 0
        inv_count = db.query(func.count(Inventory.id)).filter(Inventory.snapshot_id == s.id).scalar() or 0
        items.append(
            SnapshotRead(
                id=s.id,
                project_id=s.project_id,
                content_hash=s.content_hash,
                parser_version=s.parser_version,
                topology_status=s.topology_status,
                warnings=s.warnings,
                created_at=s.created_at,
                occurrence_count=occ_count,
                edge_count=edge_count,
                inventory_count=inv_count,
            )
        )

    return PaginatedResponse[SnapshotRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotRead)
def get_snapshot(
    snapshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve snapshot metadata and counts."""
    snapshot = get_user_snapshot(snapshot_id, current_user, db)
    occ_count = db.query(func.count(Occurrence.id)).filter(Occurrence.snapshot_id == snapshot.id).scalar() or 0
    edge_count = db.query(func.count(Edge.id)).filter(Edge.snapshot_id == snapshot.id).scalar() or 0
    inv_count = db.query(func.count(Inventory.id)).filter(Inventory.snapshot_id == snapshot.id).scalar() or 0

    return SnapshotRead(
        id=snapshot.id,
        project_id=snapshot.project_id,
        content_hash=snapshot.content_hash,
        parser_version=snapshot.parser_version,
        topology_status=snapshot.topology_status,
        warnings=snapshot.warnings,
        created_at=snapshot.created_at,
        occurrence_count=occ_count,
        edge_count=edge_count,
        inventory_count=inv_count,
    )


@router.get("/snapshots/{snapshot_id}/graph", response_model=GraphResponse)
def get_snapshot_graph(
    snapshot_id: uuid.UUID,
    limit_nodes: int = Query(500, ge=1, le=5000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return Cytoscape.js-compatible nodes and edges for visualization."""
    snapshot = get_user_snapshot(snapshot_id, current_user, db)

    total_occurrences = db.query(func.count(Occurrence.id)).filter(Occurrence.snapshot_id == snapshot.id).scalar() or 0
    total_edges = db.query(func.count(Edge.id)).filter(Edge.snapshot_id == snapshot.id).scalar() or 0

    # Fetch snapshot assets
    snap_assets = db.query(SnapshotAsset).filter(SnapshotAsset.snapshot_id == snapshot.id).all()
    asset_roots = {sa.root_ref: sa for sa in snap_assets}

    # Fetch occurrences
    occurrences = (
        db.query(Occurrence)
        .filter(Occurrence.snapshot_id == snapshot.id)
        .limit(limit_nodes)
        .all()
    )

    nodes: List[GraphNode] = []
    included_refs = set()

    # Add asset root nodes
    for root_ref, sa in asset_roots.items():
        nodes.append(
            GraphNode(
                id=root_ref,
                label=sa.environment_context.get("asset_name", root_ref),
                kind="root",
                name=sa.environment_context.get("asset_name", root_ref),
                asset_id=sa.asset_id,
                environment=sa.environment_context.get("environment", "production"),
                metadata={"captured_weight": sa.captured_weight},
            )
        )
        included_refs.add(root_ref)

    for o in occurrences:
        meta = o.metadata_json or {}
        kind = "root" if o.local_ref in asset_roots else "occurrence"
        nodes.append(
            GraphNode(
                id=o.local_ref,
                label=f"{meta.get('name', o.local_ref)}@{meta.get('version', '')}",
                kind=kind,
                name=meta.get("name", o.local_ref),
                version=meta.get("version"),
                ecosystem=meta.get("ecosystem"),
                purl=meta.get("canonical_purl"),
                metadata=meta,
            )
        )
        included_refs.add(o.local_ref)

    # Fetch edges between included nodes
    edges = db.query(Edge).filter(Edge.snapshot_id == snapshot.id).all()
    graph_edges: List[GraphEdge] = []

    for e in edges:
        # Only include edges where both endpoints are in nodes
        if e.from_ref in included_refs and e.to_ref in included_refs:
            graph_edges.append(
                GraphEdge(
                    id=str(e.id),
                    source=e.from_ref,
                    target=e.to_ref,
                    gate_default=e.gate_default,
                    context=e.context or {},
                    provenance=e.provenance,
                )
            )

    is_truncated = total_occurrences > len(occurrences)

    return GraphResponse(
        snapshot_id=snapshot.id,
        nodes=nodes,
        edges=graph_edges,
        is_truncated=is_truncated,
        total_nodes=total_occurrences + len(asset_roots),
        total_edges=total_edges,
        topology_status=snapshot.topology_status,
        warnings=snapshot.warnings,
    )
