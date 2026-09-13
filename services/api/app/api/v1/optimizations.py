import hashlib
import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.errors import NotFoundException, ValidationException
from app.db.session import get_db
from app.db.models import (
    User,
    Snapshot,
    SnapshotAsset,
    Asset,
    Occurrence,
    Edge,
    Run,
    Control,
    OptimizationRun,
)
from app.api.v1.runs import get_user_run
from app.schemas.run import ScenarioCreate, ReachedAssetInfo, WitnessPath
from app.schemas.optimization import OptimizationRequest, OptimizationRead, CandidateControl
from app.analysis.evaluator import ReachabilityEvaluator, AssetNode
from app.optimization.optimizer import CounterfactualOptimizer
from app.reporting.exporter import ReportExporter

router = APIRouter(tags=["Optimization & Reporting"])


@router.post("/runs/{run_id}/optimizations", response_model=OptimizationRead, status_code=status.HTTP_201_CREATED)
def create_optimization(
    run_id: uuid.UUID,
    request_data: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate candidate mitigations within budget and persist optimal counterfactual outcome."""
    run_obj = get_user_run(run_id, current_user, db)
    snapshot = db.query(Snapshot).filter(Snapshot.id == run_obj.snapshot_id).first()
    if not snapshot:
        raise NotFoundException("Snapshot not found for this run.")

    scenario = ScenarioCreate.model_validate(run_obj.scenario_json)

    # 1. Fetch graph occurrences & edges
    db_occurrences = db.query(Occurrence).filter(Occurrence.snapshot_id == snapshot.id).all()
    db_edges = db.query(Edge).filter(Edge.snapshot_id == snapshot.id).all()
    db_snapshot_assets = db.query(SnapshotAsset).filter(SnapshotAsset.snapshot_id == snapshot.id).all()

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

    evaluator = ReachabilityEvaluator(
        occurrences=occ_dicts,
        edges=edge_dicts,
        assets=asset_nodes,
        topology_status=snapshot.topology_status,
    )

    # 2. Run Counterfactual Optimizer
    optimizer = CounterfactualOptimizer(evaluator)
    outcome = optimizer.optimize(
        scenario=scenario,
        controls=request_data.candidate_controls,
        budget=request_data.budget,
    )

    # 3. Hash candidate controls for reproducibility
    raw_candidates_repr = json.dumps([c.model_dump(mode="json") for c in request_data.candidate_controls], sort_keys=True)
    candidate_hash = hashlib.sha256(raw_candidates_repr.encode("utf-8")).hexdigest()

    # 4. Persist OptimizationRun
    opt_run_id = uuid.uuid4()
    result_json = {
        "baseline_lower": outcome.baseline_lower,
        "baseline_upper": outcome.baseline_upper,
        "optimized_lower": outcome.optimized_lower,
        "optimized_upper": outcome.optimized_upper,
        "absolute_reduction": outcome.absolute_reduction,
        "relative_reduction": outcome.relative_reduction,
        "residual_assets": [a.model_dump(mode="json") for a in outcome.residual_assets],
        "residual_paths": [p.model_dump(mode="json") for p in outcome.residual_paths],
        "assumptions": outcome.assumptions,
        "side_effects": outcome.side_effects,
    }

    opt_obj = OptimizationRun(
        id=opt_run_id,
        run_id=run_obj.id,
        budget=request_data.budget,
        candidate_set_hash=candidate_hash,
        chosen_controls=[c.model_dump(mode="json") for c in outcome.chosen_controls],
        result_json=result_json,
        optimizer_version="1.0.0",
    )
    db.add(opt_obj)

    # Persist chosen controls in Control table
    for c in outcome.chosen_controls:
        db_control = Control(
            run_id=run_obj.id,
            label=c.label,
            cost=c.cost,
            edit_json={"control_type": c.control_type, "parameters": c.parameters},
            mechanism_scope=c.mechanism_scope,
            assumptions=c.assumptions,
        )
        db.add(db_control)

    db.commit()
    db.refresh(opt_obj)

    return OptimizationRead(
        id=opt_obj.id,
        run_id=opt_obj.run_id,
        budget=opt_obj.budget,
        candidate_set_hash=opt_obj.candidate_set_hash,
        chosen_controls=outcome.chosen_controls,
        total_cost=outcome.total_cost,
        baseline_lower=outcome.baseline_lower,
        baseline_upper=outcome.baseline_upper,
        optimized_lower=outcome.optimized_lower,
        optimized_upper=outcome.optimized_upper,
        absolute_reduction=outcome.absolute_reduction,
        relative_reduction=outcome.relative_reduction,
        residual_assets=outcome.residual_assets,
        residual_paths=outcome.residual_paths,
        assumptions=outcome.assumptions,
        side_effects=outcome.side_effects,
        optimizer_version=opt_obj.optimizer_version,
        created_at=opt_obj.created_at,
    )


@router.get("/runs/{run_id}/export")
def export_run_report(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download self-contained, immutable versioned JSON report."""
    run_obj = get_user_run(run_id, current_user, db)
    snapshot = db.query(Snapshot).filter(Snapshot.id == run_obj.snapshot_id).first()
    if not snapshot:
        raise NotFoundException("Snapshot not found for this run.")

    # Check for latest optimization run
    latest_opt = (
        db.query(OptimizationRun)
        .filter(OptimizationRun.run_id == run_obj.id)
        .order_by(OptimizationRun.created_at.desc())
        .first()
    )

    opt_data = None
    if latest_opt:
        opt_res = latest_opt.result_json or {}
        chosen = [CandidateControl.model_validate(c) for c in (latest_opt.chosen_controls or [])]
        opt_data = {
            "id": str(latest_opt.id),
            "budget": latest_opt.budget,
            "total_cost": sum(c.cost for c in chosen),
            "chosen_controls": [c.model_dump(mode="json") for c in chosen],
            "optimizer_version": latest_opt.optimizer_version,
            "optimized_lower": opt_res.get("optimized_lower"),
            "optimized_upper": opt_res.get("optimized_upper"),
            "absolute_reduction": opt_res.get("absolute_reduction"),
            "relative_reduction": opt_res.get("relative_reduction"),
            "residual_assets": opt_res.get("residual_assets", []),
            "residual_paths": opt_res.get("residual_paths", []),
            "side_effects": opt_res.get("side_effects", []),
        }

    run_data = {
        "run_id": str(run_obj.id),
        "snapshot_id": str(run_obj.snapshot_id),
        "model_version": run_obj.graph_model_version,
        "scenario": run_obj.scenario_json,
        "lower_index": (run_obj.result_json or {}).get("lower_index", 0.0),
        "upper_index": (run_obj.result_json or {}).get("upper_index", 0.0),
        "total_scoped_weight": (run_obj.result_json or {}).get("total_scoped_weight", 0),
        "reached_assets": (run_obj.result_json or {}).get("reached_assets", []),
        "witness_paths": (run_obj.result_json or {}).get("witness_paths", []),
        "assumptions": (run_obj.result_json or {}).get("assumptions", []),
    }

    snapshot_metadata = {
        "content_hash": snapshot.content_hash,
        "created_at": snapshot.created_at.isoformat(),
        "topology_status": snapshot.topology_status,
        "warnings": snapshot.warnings or [],
    }

    report = ReportExporter.export_run_report(
        run_data=run_data,
        snapshot_metadata=snapshot_metadata,
        optimization_data=opt_data,
    )

    headers = {
        "Content-Disposition": f"attachment; filename=rippleguard-run-{run_id}.json",
    }
    return JSONResponse(content=report, headers=headers)
