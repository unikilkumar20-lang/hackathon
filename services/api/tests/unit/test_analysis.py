import uuid
import pytest
from app.analysis.evaluator import ReachabilityEvaluator, AssetNode
from app.schemas.run import ScenarioCreate, SourceSpec, GateOverride


def test_reachability_basic_invariants():
    assets = [
        AssetNode(asset_id="asset-1", name="App One", environment="production", weight=4, root_ref="app-1"),
        AssetNode(asset_id="asset-2", name="App Two", environment="production", weight=2, root_ref="app-2"),
    ]

    occurrences = [
        {"local_ref": "app-1", "name": "app-1", "version": "1.0.0"},
        {"local_ref": "app-2", "name": "app-2", "version": "1.0.0"},
        {"local_ref": "shared-lib", "name": "shared-lib", "version": "1.0.0"},
        {"local_ref": "deep-dep", "name": "deep-dep", "version": "1.0.0"},
    ]

    edges = [
        # app-1 consumes shared-lib (gate: true)
        {"id": "e1", "from_ref": "app-1", "to_ref": "shared-lib", "gate_default": "true"},
        # shared-lib consumes deep-dep (gate: true)
        {"id": "e2", "from_ref": "shared-lib", "to_ref": "deep-dep", "gate_default": "true"},
        # app-2 consumes shared-lib (gate: unknown)
        {"id": "e3", "from_ref": "app-2", "to_ref": "shared-lib", "gate_default": "unknown"},
    ]

    evaluator = ReachabilityEvaluator(occurrences, edges, assets)

    scenario = ScenarioCreate(
        snapshot_id=uuid.uuid4(),
        source=SourceSpec(kind="occurrence", id="deep-dep"),
        mode="runtime",
    )

    res = evaluator.evaluate_scenario(scenario)

    # Invariants
    assert 0 <= res.lower_index <= res.upper_index <= 100
    assert res.total_scoped_weight == 6  # 4 + 2

    # App-1 is reached in both lower and upper (all gates are true: deep-dep -> shared-lib -> app-1)
    # App-2 is reached in upper only (e3 gate is unknown)
    # Lower weight = 4 -> 4/6 = 66.67%
    # Upper weight = 6 -> 6/6 = 100.0%
    assert res.lower_index == 66.67
    assert res.upper_index == 100.0

    # Test Gate Override: override e3 to false
    scenario_with_override = ScenarioCreate(
        snapshot_id=scenario.snapshot_id,
        source=scenario.source,
        mode="runtime",
        gate_overrides=[
            GateOverride(target_type="edge", target_id="e3", value="false", reason="Execution blocked")
        ],
    )
    res_override = evaluator.evaluate_scenario(scenario_with_override)

    # Now App-2 is blocked in both lower and upper!
    # Upper index drops to 66.67%
    assert res_override.lower_index == 66.67
    assert res_override.upper_index == 66.67


def test_cycle_termination_safety():
    assets = [
        AssetNode(asset_id="asset-1", name="App One", environment="production", weight=3, root_ref="app-1")
    ]

    occurrences = [
        {"local_ref": "app-1", "name": "app-1"},
        {"local_ref": "node-a", "name": "node-a"},
        {"local_ref": "node-b", "name": "node-b"},
        {"local_ref": "node-c", "name": "node-c"},
    ]

    # Cyclical dependency: app-1 -> node-a -> node-b -> node-c -> node-a
    edges = [
        {"id": "e1", "from_ref": "app-1", "to_ref": "node-a", "gate_default": "true"},
        {"id": "e2", "from_ref": "node-a", "to_ref": "node-b", "gate_default": "true"},
        {"id": "e3", "from_ref": "node-b", "to_ref": "node-c", "gate_default": "true"},
        {"id": "e4", "from_ref": "node-c", "to_ref": "node-a", "gate_default": "true"},
    ]

    evaluator = ReachabilityEvaluator(occurrences, edges, assets)

    scenario = ScenarioCreate(
        snapshot_id=uuid.uuid4(),
        source=SourceSpec(kind="occurrence", id="node-c"),
        mode="runtime",
    )

    # Must terminate cleanly without infinite loop or RecursionError
    res = evaluator.evaluate_scenario(scenario)
    assert res.lower_index == 100.0
    assert res.upper_index == 100.0
    assert len(res.witness_paths) == 1
