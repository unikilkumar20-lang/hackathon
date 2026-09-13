import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.auth import get_current_user
from app.core.errors import NotFoundException
from app.db.session import get_db
from app.db.models import (
    User,
    Snapshot,
    PackageIdentity,
    Occurrence,
    EnrichmentCheck,
    Advisory,
    Finding,
    Evidence,
)
from app.api.v1.snapshots import get_user_snapshot
from app.schemas.enrichment import EnrichmentCheckRead, FindingRead, AdvisoryRead
from app.schemas.common import PaginatedResponse
from app.enrichment.osv_client import OSVClient

router = APIRouter(tags=["Security Enrichment"])


@router.post("/snapshots/{snapshot_id}/enrichment-checks", response_model=EnrichmentCheckRead, status_code=status.HTTP_201_CREATED)
async def create_enrichment_check(
    snapshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run OSV security advisory enrichment for packages in a snapshot."""
    snapshot = get_user_snapshot(snapshot_id, current_user, db)

    # 1. Fetch distinct package identities in snapshot
    occurrences = (
        db.query(Occurrence)
        .filter(Occurrence.snapshot_id == snapshot.id, Occurrence.package_identity_id.isnot(None))
        .all()
    )
    pkg_id_set = {o.package_identity_id for o in occurrences if o.package_identity_id}

    package_identities = (
        db.query(PackageIdentity)
        .filter(PackageIdentity.id.in_(pkg_id_set))
        .all()
        if pkg_id_set
        else []
    )

    pkg_dicts = [
        {
            "id": p.id,
            "ecosystem": p.ecosystem,
            "namespace": p.namespace,
            "name": p.name,
            "version": p.version,
            "canonical_purl": p.canonical_purl,
        }
        for p in package_identities
    ]

    # Map (ecosystem, name, version) -> PackageIdentity object
    pkg_lookup = {
        (p.ecosystem.lower(), p.name, p.version): p for p in package_identities
    }

    # 2. Query OSV
    osv_client = OSVClient()
    report = await osv_client.check_packages(pkg_dicts)

    # 3. Persist EnrichmentCheck
    check_id = uuid.uuid4()
    coverage_dict = {
        "checked_count": report.checked_count,
        "matched_count": report.matched_count,
        "failed_count": report.failed_count,
        "unsupported_count": report.unsupported_count,
    }

    check_obj = EnrichmentCheck(
        id=check_id,
        snapshot_id=snapshot.id,
        provider="osv",
        status=report.status,
        coverage=coverage_dict,
        started_at=report.started_at,
        finished_at=report.finished_at,
        error=report.error,
    )
    db.add(check_obj)
    db.flush()

    # 4. Persist Advisories, Findings, and Evidence
    findings_count = 0
    advisory_cache: Dict[str, Advisory] = {}

    for res in report.results:
        if res.status != "matches_found":
            continue

        matching_pkg = pkg_lookup.get((res.ecosystem.lower(), res.name, res.version))
        if not matching_pkg:
            continue

        for adv_match in res.advisories:
            adv_obj = advisory_cache.get(adv_match.external_id)
            if not adv_obj:
                existing_adv = (
                    db.query(Advisory)
                    .filter(Advisory.provider == "osv", Advisory.external_id == adv_match.external_id)
                    .first()
                )
                if existing_adv:
                    adv_obj = existing_adv
                else:
                    adv_obj = Advisory(
                        id=uuid.uuid4(),
                        provider="osv",
                        external_id=adv_match.external_id,
                        aliases=adv_match.aliases,
                        source_url=adv_match.source_url,
                        details=adv_match.details,
                    )
                    db.add(adv_obj)
                    db.flush()
                advisory_cache[adv_match.external_id] = adv_obj

            # Create Finding
            finding = Finding(
                id=uuid.uuid4(),
                check_id=check_obj.id,
                package_identity_id=matching_pkg.id,
                advisory_id=adv_obj.id,
                match_details={
                    "package_name": matching_pkg.name,
                    "package_version": matching_pkg.version,
                    "ecosystem": matching_pkg.ecosystem,
                    "summary": adv_match.summary,
                    "severity": adv_match.severity,
                },
            )
            db.add(finding)
            findings_count += 1

            # Create Evidence record
            evidence = Evidence(
                snapshot_id=snapshot.id,
                kind="osv_advisory",
                source_ref=f"osv:{adv_match.external_id}",
                trust_label="official_provider",
                details={
                    "advisory_id": adv_match.external_id,
                    "package": f"{matching_pkg.name}@{matching_pkg.version}",
                    "ecosystem": matching_pkg.ecosystem,
                    "summary": adv_match.summary,
                },
            )
            db.add(evidence)

    db.commit()
    db.refresh(check_obj)

    return EnrichmentCheckRead(
        id=check_obj.id,
        snapshot_id=check_obj.snapshot_id,
        provider=check_obj.provider,
        status=check_obj.status,
        coverage=check_obj.coverage,
        started_at=check_obj.started_at,
        finished_at=check_obj.finished_at,
        error=check_obj.error,
        findings_count=findings_count,
    )


@router.get("/snapshots/{snapshot_id}/findings", response_model=PaginatedResponse[FindingRead])
def list_snapshot_findings(
    snapshot_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve paginated security findings for an owned snapshot."""
    snapshot = get_user_snapshot(snapshot_id, current_user, db)

    # Query findings joined with check and package identity
    query = (
        db.query(Finding)
        .join(EnrichmentCheck, Finding.check_id == EnrichmentCheck.id)
        .join(PackageIdentity, Finding.package_identity_id == PackageIdentity.id)
        .join(Advisory, Finding.advisory_id == Advisory.id)
        .filter(EnrichmentCheck.snapshot_id == snapshot.id)
    )

    total = query.count()
    offset = (page - 1) * page_size
    findings = query.offset(offset).limit(page_size).all()

    items: List[FindingRead] = []
    for f in findings:
        adv = f.advisory
        pkg = f.package_identity
        items.append(
            FindingRead(
                id=f.id,
                check_id=f.check_id,
                package_identity_id=f.package_identity_id,
                package_name=pkg.name,
                package_version=pkg.version,
                ecosystem=pkg.ecosystem,
                canonical_purl=pkg.canonical_purl,
                advisory=AdvisoryRead(
                    id=adv.id,
                    provider=adv.provider,
                    external_id=adv.external_id,
                    aliases=adv.aliases or [],
                    source_url=adv.source_url,
                    details=adv.details or {},
                    retrieved_at=adv.retrieved_at,
                ),
                match_details=f.match_details or {},
            )
        )

    return PaginatedResponse[FindingRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )
