import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.errors import NotFoundException, ValidationException
from app.db.session import get_db
from app.db.models import (
    User,
    Project,
    Snapshot,
    SnapshotAsset,
    Asset,
    Occurrence,
    Edge,
    Run,
    Evidence,
)
from app.api.v1.snapshots import get_user_snapshot
from app.schemas.run import (
    ScenarioCreate,
    RunRead,
    EvidenceRead,
    ReachedAssetInfo,
    WitnessPath,
)
from app.analysis.evaluator import ReachabilityEvaluator, AssetNode

router = APIRouter(prefix="/runs", tags=["Runs & Scenarios"])


def get_user_run(run_id: uuid.UUID, user: User, db: Session) -> Run:
    """Retrieve run by ID, verifying user owns the snapshot's parent project. Fails closed with 404."""
    run = (
        db.query(Run)
        .join(Snapshot, Run.snapshot_id == Snapshot.id)
        .join(Project, Snapshot.project_id == Project.id)
        .filter(Run.id == run_id, Project.owner_user_id == user.id)
        .first()
    )
    if not run:
        raise NotFoundException(message=f"Run '{run_id}' not found.")
    return run


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    scenario: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate compromise scenario exposure reachability and save immutable run."""
    snapshot = get_user_snapshot(scenario.snapshot_id, current_user, db)

    # 1. Fetch occurrences and edges
    db_occurrences = db.query(Occurrence).filter(Occurrence.snapshot_id == snapshot.id).all()
    db_edges = db.query(Edge).filter(Edge.snapshot_id == snapshot.id).all()
    db_snapshot_assets = db.query(SnapshotAsset).filter(SnapshotAsset.snapshot_id == snapshot.id).all()

    if not db_occurrences:
        raise ValidationException("Snapshot has no occurrences to evaluate.")

    # 2. Build asset nodes
    asset_nodes: List[AssetNode] = []
    for sa in db_snapshot_assets:
        asset_obj = db.query(Asset).filter(Asset.id == sa.asset_id).first()
        asset_name = asset_obj.name if asset_obj else sa.environment_context.get("asset_name", str(sa.asset_id))
        env = asset_obj.environment if asset_obj else sa.environment_context.get("environment", "production")

        asset_nodes.append(
            AssetNode(
                asset_id=str(sa.asset_id),
                name=asset_name,
                environment=env,
                weight=sa.captured_weight,
                root_ref=sa.root_ref,
            )
        )

    # Convert occurrences & edges to evaluator dicts
    occ_dicts = [
        {
            "local_ref": o.local_ref,
            "package_identity_id": str(o.package_identity_id) if o.package_identity_id else None,
            "name": (o.metadata_json or {}).get("name", o.local_ref),
            "version": (o.metadata_json or {}).get("version"),
            "metadata_json": o.metadata_json or {},
        }
        for o in db_occurrences
    ]

    edge_dicts = [
        {
            "id": str(e.id),
            "from_ref": e.from_ref,
            "to_ref": e.to_ref,
            "gate_default": e.gate_default,
            "context": e.context or {},
            "provenance": e.provenance,
        }
        for e in db_edges
    ]

    # 3. Evaluate reachability
    evaluator = ReachabilityEvaluator(
        occurrences=occ_dicts,
        edges=edge_dicts,
        assets=asset_nodes,
        topology_status=snapshot.topology_status,
    )

    result = evaluator.evaluate_scenario(scenario)

    # 4. Persist Run
    run_id = uuid.uuid4()
    scenario_json = scenario.model_dump(mode="json")
    result_json = {
        "lower_index": result.lower_index,
        "upper_index": result.upper_index,
        "total_scoped_weight": result.total_scoped_weight,
        "reached_assets": [a.model_dump(mode="json") for a in result.reached_assets],
        "witness_paths": [p.model_dump(mode="json") for p in result.witness_paths],
        "assumptions": result.assumptions,
        "topology_warnings": result.topology_warnings,
    }

    run_obj = Run(
        id=run_id,
        snapshot_id=snapshot.id,
        scenario_json=scenario_json,
        result_json=result_json,
        graph_model_version="1.0.0",
    )
    db.add(run_obj)

    # Persist evidence for witness paths
    evidence_ids: List[uuid.UUID] = []
    if result.witness_paths:
        ev = Evidence(
            snapshot_id=snapshot.id,
            kind="witness_path",
            source_ref=str(run_id),
            trust_label="deterministic_traversal",
            details={
                "witness_paths_count": len(result.witness_paths),
                "lower_index": result.lower_index,
                "upper_index": result.upper_index,
            },
        )
        db.add(ev)
        db.flush()
        evidence_ids.append(ev.id)

    db.commit()
    db.refresh(run_obj)

    return RunRead(
        id=run_obj.id,
        snapshot_id=run_obj.snapshot_id,
        scenario=scenario,
        model_version=run_obj.graph_model_version,
        lower_index=result.lower_index,
        upper_index=result.upper_index,
        total_scoped_weight=result.total_scoped_weight,
        reached_assets=result.reached_assets,
        witness_paths=result.witness_paths,
        evidence_ids=evidence_ids,
        assumptions=result.assumptions,
        topology_warnings=result.topology_warnings,
        created_at=run_obj.created_at,
    )


@router.get("/{run_id}", response_model=RunRead)
def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve saved run details, exposure indices, and witness paths."""
    run_obj = get_user_run(run_id, current_user, db)
    scenario_dict = run_obj.scenario_json or {}
    res = run_obj.result_json or {}

    scenario = ScenarioCreate.model_validate(scenario_dict)
    reached_assets = [ReachedAssetInfo.model_validate(a) for a in res.get("reached_assets", [])]
    witness_paths = [WitnessPath.model_validate(p) for p in res.get("witness_paths", [])]

    # Find associated evidence IDs
    ev_ids = [
        e.id
        for e in db.query(Evidence)
        .filter(Evidence.snapshot_id == run_obj.snapshot_id, Evidence.source_ref == str(run_obj.id))
        .all()
    ]

    return RunRead(
        id=run_obj.id,
        snapshot_id=run_obj.snapshot_id,
        scenario=scenario,
        model_version=run_obj.graph_model_version,
        lower_index=float(res.get("lower_index", 0.0)),
        upper_index=float(res.get("upper_index", 0.0)),
        total_scoped_weight=int(res.get("total_scoped_weight", 0)),
        reached_assets=reached_assets,
        witness_paths=witness_paths,
        evidence_ids=ev_ids,
        assumptions=res.get("assumptions", []),
        topology_warnings=res.get("topology_warnings", []),
        created_at=run_obj.created_at,
    )


@router.get("/{run_id}/evidence", response_model=List[EvidenceRead])
def get_run_evidence(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve evidence items associated with this run's snapshot."""
    run_obj = get_user_run(run_id, current_user, db)
    evidences = db.query(Evidence).filter(Evidence.snapshot_id == run_obj.snapshot_id).all()
    return [EvidenceRead.model_validate(e) for e in evidences]
