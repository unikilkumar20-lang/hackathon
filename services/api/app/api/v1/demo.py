import json
import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, Body, status
from pydantic import BaseModel, Field

from app.schemas.run import ScenarioCreate, SourceSpec, GateOverride, ReachedAssetInfo, WitnessPath
from app.schemas.optimization import CandidateControl, OptimizationRequest, OptimizationRead
from app.analysis.evaluator import ReachabilityEvaluator, AssetNode, TraversalResult
from app.optimization.optimizer import CounterfactualOptimizer

router = APIRouter(prefix="/demo", tags=["Synthetic Demo"])

FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "fixtures", "synthetic-demo", "multi_app_fixture.json")
)


def load_fixture() -> Dict[str, Any]:
    """Load PRD Section 17 synthetic multi-app fixture."""
    if not os.path.exists(FIXTURE_PATH):
        raise FileNotFoundError(f"Synthetic fixture not found at {FIXTURE_PATH}")
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_fixture_evaluator(fixture_data: Dict[str, Any]) -> ReachabilityEvaluator:
    """Build ReachabilityEvaluator directly from synthetic fixture."""
    asset_nodes = [
        AssetNode(
            asset_id=a["asset_id"],
            name=a["name"],
            environment=a["environment"],
            weight=a["weight"],
            root_ref=a["root_ref"],
        )
        for a in fixture_data["assets"]
    ]

    return ReachabilityEvaluator(
        occurrences=fixture_data["occurrences"],
        edges=fixture_data["edges"],
        assets=asset_nodes,
        topology_status="complete",
    )


class DemoScenarioRequest(BaseModel):
    mode: str = Field(default="runtime", description="'runtime' or 'install-script-only'")
    source_ref: str = Field(default="tiny-parse@1.0.0")
    asset_weights: Optional[Dict[str, int]] = None
    gate_overrides: List[GateOverride] = Field(default_factory=list)


class DemoEvaluationResponse(BaseModel):
    disclaimer: str
    lower_index: float
    upper_index: float
    total_scoped_weight: int
    reached_assets: List[ReachedAssetInfo]
    witness_paths: List[WitnessPath]
    assumptions: List[str]


@router.get("/fixture")
def get_demo_fixture():
    """Retrieve PRD Section 17 synthetic multi-app fixture with baseline metrics."""
    data = load_fixture()
    evaluator = build_fixture_evaluator(data)

    # Compute default baseline
    scenario = ScenarioCreate(
        snapshot_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        source=SourceSpec(kind="occurrence", id=data["source_package"]["local_ref"]),
        mode="runtime",
    )
    res = evaluator.evaluate_scenario(scenario)

    return {
        "disclaimer": data["disclaimer"],
        "name": data["name"],
        "source_package": data["source_package"],
        "baseline_metrics": {
            "lower_index": res.lower_index,  # 66.7
            "upper_index": res.upper_index,  # 72.2
            "total_scoped_weight": res.total_scoped_weight,  # 18
            "reached_assets": [a.model_dump() for a in res.reached_assets],
            "witness_paths": [p.model_dump() for p in res.witness_paths],
        },
        "assets": data["assets"],
        "occurrences": data["occurrences"],
        "edges": data["edges"],
        "candidate_controls": data["candidate_controls"],
    }


@router.post("/evaluate", response_model=DemoEvaluationResponse)
def evaluate_demo_scenario(req: DemoScenarioRequest = Body(...)):
    """Evaluate interactive scenario parameters dynamically on the synthetic fixture."""
    data = load_fixture()
    evaluator = build_fixture_evaluator(data)

    scenario = ScenarioCreate(
        snapshot_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        source=SourceSpec(kind="occurrence", id=req.source_ref),
        mode=req.mode,  # type: ignore
        asset_weights=req.asset_weights,
        gate_overrides=req.gate_overrides,
    )

    res = evaluator.evaluate_scenario(scenario)

    return DemoEvaluationResponse(
        disclaimer=data["disclaimer"],
        lower_index=res.lower_index,
        upper_index=res.upper_index,
        total_scoped_weight=res.total_scoped_weight,
        reached_assets=res.reached_assets,
        witness_paths=res.witness_paths,
        assumptions=res.assumptions,
    )


@router.post("/optimize")
def optimize_demo_controls(
    budget: int = Query(3, ge=0),
    mode: str = Query("runtime"),
):
    """Run counterfactual mitigation optimization directly on the synthetic demo fixture."""
    data = load_fixture()
    evaluator = build_fixture_evaluator(data)

    scenario = ScenarioCreate(
        snapshot_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        source=SourceSpec(kind="occurrence", id=data["source_package"]["local_ref"]),
        mode=mode,  # type: ignore
    )

    candidate_controls = [CandidateControl.model_validate(c) for c in data["candidate_controls"]]
    optimizer = CounterfactualOptimizer(evaluator)
    outcome = optimizer.optimize(scenario, candidate_controls, budget=budget)

    return {
        "disclaimer": data["disclaimer"],
        "budget": budget,
        "mode": mode,
        "chosen_controls": [c.model_dump() for c in outcome.chosen_controls],
        "total_cost": outcome.total_cost,
        "baseline_lower": outcome.baseline_lower,
        "baseline_upper": outcome.baseline_upper,
        "optimized_lower": outcome.optimized_lower,
        "optimized_upper": outcome.optimized_upper,
        "absolute_reduction": outcome.absolute_reduction,
        "relative_reduction": outcome.relative_reduction,
        "residual_assets": [a.model_dump() for a in outcome.residual_assets],
        "residual_paths": [p.model_dump() for p in outcome.residual_paths],
        "side_effects": outcome.side_effects,
        "assumptions": outcome.assumptions,
    }
