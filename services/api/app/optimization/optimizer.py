import hashlib
import itertools
from typing import List, Set, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from app.schemas.optimization import CandidateControl, OptimizationRead
from app.schemas.run import ScenarioCreate, ReachedAssetInfo, WitnessPath
from app.analysis.evaluator import ReachabilityEvaluator, TraversalResult


@dataclass
class OptimizedOutcome:
    chosen_controls: List[CandidateControl]
    total_cost: int
    baseline_lower: float
    baseline_upper: float
    optimized_lower: float
    optimized_upper: float
    absolute_reduction: float
    relative_reduction: Optional[float]
    residual_assets: List[ReachedAssetInfo]
    residual_paths: List[WitnessPath]
    assumptions: List[str]
    side_effects: List[str]


class CounterfactualOptimizer:
    """Exact power-set mitigation optimizer for up to 8 candidate controls (PRD Section 10)."""

    def __init__(self, evaluator: ReachabilityEvaluator):
        self.evaluator = evaluator

    def optimize(
        self,
        scenario: ScenarioCreate,
        controls: List[CandidateControl],
        budget: int,
    ) -> OptimizedOutcome:
        # 1. Baseline evaluation (empty set of controls)
        baseline = self.evaluator.evaluate_scenario(scenario)
        baseline_lower = baseline.lower_index
        baseline_upper = baseline.upper_index

        if not controls or budget <= 0:
            return OptimizedOutcome(
                chosen_controls=[],
                total_cost=0,
                baseline_lower=baseline_lower,
                baseline_upper=baseline_upper,
                optimized_lower=baseline_lower,
                optimized_upper=baseline_upper,
                absolute_reduction=0.0,
                relative_reduction=0.0 if baseline_upper > 0 else None,
                residual_assets=baseline.reached_assets,
                residual_paths=baseline.witness_paths,
                assumptions=baseline.assumptions + ["No controls applied or zero budget provided."],
                side_effects=[],
            )

        # 2. Bound candidates to at most 8 controls
        candidate_controls = controls[:8]

        # 3. Enumerate power set of feasible subsets
        best_subset: Tuple[CandidateControl, ...] = ()
        best_cost: int = 0
        best_result: TraversalResult = baseline
        best_upper: float = baseline_upper
        best_lower: float = baseline_lower

        # Evaluate subsets ordered by subset size from 0 to N
        for r in range(len(candidate_controls) + 1):
            for subset in itertools.combinations(candidate_controls, r):
                subset_cost = sum(c.cost for c in subset)
                if subset_cost > budget:
                    continue

                # Prepare mitigation parameters
                disabled_scripts: Set[str] = set()
                cut_edges: Set[str] = set()
                removed_nodes: Set[str] = set()
                side_effects: List[str] = []

                for c in subset:
                    ctype = c.control_type
                    params = c.parameters or {}

                    if ctype == "disable_lifecycle_scripts":
                        asset_id = str(params.get("asset_id", ""))
                        if asset_id:
                            disabled_scripts.add(asset_id)
                        else:
                            # If no asset_id specified, disable on all scoped assets
                            for a in self.evaluator.assets:
                                disabled_scripts.add(a)
                        side_effects.append(f"Lifecycle scripts disabled for target build environments ({c.label}).")

                    elif ctype == "exclude_dependency_route":
                        edge_id = str(params.get("edge_id", ""))
                        if edge_id:
                            cut_edges.add(edge_id)
                        from_ref = str(params.get("from_ref", ""))
                        to_ref = str(params.get("to_ref", ""))
                        if from_ref and to_ref:
                            cut_edges.add(f"{from_ref}->{to_ref}")
                        side_effects.append(f"Dependency edge excluded: {c.label} (potential functionality break).")

                    elif ctype == "replace_occurrence":
                        occ_ref = str(params.get("occurrence_ref", ""))
                        if occ_ref:
                            removed_nodes.add(occ_ref)
                        side_effects.append(f"Occurrence simulated replaced/removed: {c.label}.")

                    elif ctype == "remove_package_version":
                        pkg_id = str(params.get("package_identity_id", ""))
                        pkg_name = str(params.get("package_name", ""))
                        for ref, o in self.evaluator.occurrences_map.items():
                            if str(o.get("package_identity_id")) == pkg_id or o.get("name") == pkg_name:
                                removed_nodes.add(ref)
                        side_effects.append(f"All occurrences of package simulated removed: {c.label}.")

                # Evaluate graph under this combination of controls
                res = self.evaluator.evaluate_scenario(
                    scenario=scenario,
                    disabled_script_assets=disabled_scripts,
                    cut_edges=cut_edges,
                    removed_nodes=removed_nodes,
                )

                # Tie-breaking rules (PRD Section 10):
                # 1. Lower upper_index
                # 2. Lower total effort (cost)
                # 3. Lower lower_index
                # 4. Lexicographically sorted control IDs
                is_better = False
                if res.upper_index < best_upper:
                    is_better = True
                elif res.upper_index == best_upper:
                    if subset_cost < best_cost:
                        is_better = True
                    elif subset_cost == best_cost and res.lower_index < best_lower:
                        is_better = True
                    elif subset_cost == best_cost and res.lower_index == best_lower:
                        curr_ids = sorted([c.id for c in subset])
                        best_ids = sorted([c.id for c in best_subset])
                        if curr_ids < best_ids:
                            is_better = True

                if is_better:
                    best_subset = subset
                    best_cost = subset_cost
                    best_result = res
                    best_upper = res.upper_index
                    best_lower = res.lower_index

        absolute_reduction = round(baseline_upper - best_upper, 2)
        relative_reduction = None
        if baseline_upper > 0:
            relative_reduction = round((absolute_reduction / baseline_upper) * 100.0, 2)

        # Collect chosen side-effects & assumptions
        chosen_side_effects: List[str] = []
        for c in best_subset:
            chosen_side_effects.append(f"Control '{c.label}': effort {c.cost} units. Scope: {c.mechanism_scope}.")

        assumptions = list(best_result.assumptions)
        if best_upper == 0.0:
            assumptions.append("Result is 0% upper exposure: no modeled exposure under this scenario (not a guarantee of absolute safety).")

        return OptimizedOutcome(
            chosen_controls=list(best_subset),
            total_cost=best_cost,
            baseline_lower=baseline_lower,
            baseline_upper=baseline_upper,
            optimized_lower=best_lower,
            optimized_upper=best_upper,
            absolute_reduction=absolute_reduction,
            relative_reduction=relative_reduction,
            residual_assets=best_result.reached_assets,
            residual_paths=best_result.witness_paths,
            assumptions=assumptions,
            side_effects=chosen_side_effects,
        )
