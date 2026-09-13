import uuid
import pytest
from app.analysis.evaluator import ReachabilityEvaluator, AssetNode
from app.optimization.optimizer import CounterfactualOptimizer
from app.schemas.run import ScenarioCreate, SourceSpec
from app.schemas.optimization import CandidateControl


def test_parallel_route_synergy():
    """Verify that parallel routes require both cuts and optimizer identifies the combination."""
    assets = [
        AssetNode(asset_id="asset-checkout", name="Checkout", environment="production", weight=5, root_ref="checkout-app")
    ]

    occurrences = [
        {"local_ref": "checkout-app", "name": "checkout-app"},
        {"local_ref": "route-a", "name": "route-a"},
        {"local_ref": "route-b", "name": "route-b"},
        {"local_ref": "vulnerable-lib", "name": "vulnerable-lib"},
    ]

    # Two parallel routes from checkout-app to vulnerable-lib:
    # 1. checkout-app -> route-a -> vulnerable-lib
    # 2. checkout-app -> route-b -> vulnerable-lib
    edges = [
        {"id": "e-a1", "from_ref": "checkout-app", "to_ref": "route-a", "gate_default": "true"},
        {"id": "e-a2", "from_ref": "route-a", "to_ref": "vulnerable-lib", "gate_default": "true"},
        {"id": "e-b1", "from_ref": "checkout-app", "to_ref": "route-b", "gate_default": "true"},
        {"id": "e-b2", "from_ref": "route-b", "to_ref": "vulnerable-lib", "gate_default": "true"},
    ]

    evaluator = ReachabilityEvaluator(occurrences, edges, assets)
    optimizer = CounterfactualOptimizer(evaluator)

    scenario = ScenarioCreate(
        snapshot_id=uuid.uuid4(),
        source=SourceSpec(kind="occurrence", id="vulnerable-lib"),
        mode="runtime",
    )

    controls = [
        CandidateControl(
            id="cut-route-a",
            label="Cut Route A",
            cost=2,
            control_type="exclude_dependency_route",
            parameters={"edge_id": "e-a2"},
        ),
        CandidateControl(
            id="cut-route-b",
            label="Cut Route B",
            cost=2,
            control_type="exclude_dependency_route",
            parameters={"edge_id": "e-b2"},
        ),
    ]

    # With budget = 2, can only afford one cut -> Checkout is STILL reached via the other route!
    # Expected: 0% reduction
    res_budget_2 = optimizer.optimize(scenario, controls, budget=2)
    assert res_budget_2.optimized_upper == 100.0
    assert res_budget_2.absolute_reduction == 0.0

    # With budget = 4, both cuts are affordable -> Parallel route cut -> Exposure drops to 0.0%!
    res_budget_4 = optimizer.optimize(scenario, controls, budget=4)
    assert res_budget_4.total_cost == 4
    assert len(res_budget_4.chosen_controls) == 2
    assert res_budget_4.optimized_upper == 0.0
    assert res_budget_4.absolute_reduction == 100.0
    assert res_budget_4.relative_reduction == 100.0


def test_zero_baseline_relative_reduction():
    assets = [
        AssetNode(asset_id="asset-disconnected", name="Disconnected", environment="production", weight=3, root_ref="disc-app")
    ]
    occurrences = [
        {"local_ref": "disc-app", "name": "disc-app"},
        {"local_ref": "lib-x", "name": "lib-x"},
    ]
    edges = []  # No edges

    evaluator = ReachabilityEvaluator(occurrences, edges, assets)
    optimizer = CounterfactualOptimizer(evaluator)

    scenario = ScenarioCreate(
        snapshot_id=uuid.uuid4(),
        source=SourceSpec(kind="occurrence", id="lib-x"),
        mode="runtime",
    )

    res = optimizer.optimize(scenario, [], budget=5)
    assert res.baseline_upper == 0.0
    assert res.relative_reduction is None  # PRD: None if baseline is zero, not division by zero
