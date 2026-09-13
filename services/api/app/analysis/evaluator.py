import networkx as nx
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

from app.schemas.run import (
    ScenarioCreate,
    WitnessPath,
    WitnessPathNode,
    WitnessPathEdge,
    ReachedAssetInfo,
)


@dataclass
class AssetNode:
    asset_id: str
    name: str
    environment: str
    weight: int
    root_ref: str


@dataclass
class TraversalResult:
    lower_index: float
    upper_index: float
    total_scoped_weight: int
    reached_assets: List[ReachedAssetInfo]
    witness_paths: List[WitnessPath]
    assumptions: List[str]
    topology_warnings: List[str]


class ReachabilityEvaluator:
    """Directed graph exposure reachability evaluator implementing PRD Section 9."""

    def __init__(
        self,
        occurrences: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        assets: List[AssetNode],
        topology_status: str = "complete",
    ):
        self.occurrences_map = {o["local_ref"]: o for o in occurrences}
        self.edges = edges
        self.assets = {a.asset_id: a for a in assets}
        self.assets_by_root = {a.root_ref: a for a in assets}
        self.topology_status = topology_status

        # Build directed graph: Consumer -> Dependency
        self.g = nx.DiGraph()

        # Add occurrence nodes
        for o in occurrences:
            self.g.add_node(
                o["local_ref"],
                kind="occurrence",
                name=o.get("name", o["local_ref"]),
                version=o.get("version"),
                package_identity_id=o.get("package_identity_id"),
                metadata=o.get("metadata_json", {}),
            )

        # Add asset root nodes
        for a in assets:
            self.g.add_node(
                a.root_ref,
                kind="root",
                asset_id=a.asset_id,
                name=a.name,
                environment=a.environment,
                weight=a.weight,
            )

        # Add directed edges: from_ref (consumer) -> to_ref (dependency)
        for e in edges:
            self.g.add_edge(
                e["from_ref"],
                e["to_ref"],
                id=str(e.get("id", f"{e['from_ref']}->{e['to_ref']}")),
                gate_default=e.get("gate_default", "unknown"),
                context=e.get("context", {}),
                provenance=e.get("provenance", "cyclonedx-manifest"),
            )

    def evaluate_scenario(
        self,
        scenario: ScenarioCreate,
        disabled_script_assets: Optional[Set[str]] = None,
        cut_edges: Optional[Set[str]] = None,
        removed_nodes: Optional[Set[str]] = None,
    ) -> TraversalResult:
        """Evaluate exposure reachability under a given scenario, with optional mitigation cuts."""
        assumptions: List[str] = []
        topology_warnings: List[str] = []
        disabled_script_assets = disabled_script_assets or set()
        cut_edges = cut_edges or set()
        removed_nodes = removed_nodes or set()

        if self.topology_status != "complete":
            topology_warnings.append(
                f"Snapshot topology status is '{self.topology_status}'. Graph bounds do not account for unmapped edges."
            )

        # 1. Determine scoped assets and weights
        scoped_asset_ids = scenario.asset_ids
        if scoped_asset_ids:
            target_assets = [a for aid, a in self.assets.items() if aid in [str(x) for x in scoped_asset_ids]]
        else:
            target_assets = list(self.assets.values())

        # Apply weight overrides if provided
        scoped_weights: Dict[str, int] = {}
        total_scoped_weight = 0
        for a in target_assets:
            w = a.weight
            if scenario.asset_weights and str(a.asset_id) in scenario.asset_weights:
                w = max(1, min(5, scenario.asset_weights[str(a.asset_id)]))
            scoped_weights[a.asset_id] = w
            total_scoped_weight += w

        if total_scoped_weight == 0:
            return TraversalResult(
                lower_index=0.0,
                upper_index=0.0,
                total_scoped_weight=0,
                reached_assets=[],
                witness_paths=[],
                assumptions=["No assets scoped or total weight is zero."],
                topology_warnings=topology_warnings,
            )

        # 2. Identify source occurrence nodes
        source_nodes: List[str] = []
        src = scenario.source
        if src.kind == "occurrence":
            if src.id in self.occurrences_map and src.id not in removed_nodes:
                source_nodes.append(src.id)
            else:
                # Check by name/ref match
                for ref in self.occurrences_map:
                    if ref == src.id and ref not in removed_nodes:
                        source_nodes.append(ref)
        elif src.kind == "package_identity":
            # Match package identity ID or package name
            for ref, o in self.occurrences_map.items():
                if ref in removed_nodes:
                    continue
                if str(o.get("package_identity_id")) == str(src.id) or o.get("name") == src.id:
                    source_nodes.append(ref)
                    if src.scope == "single_occurrence":
                        break

        if not source_nodes:
            assumptions.append(f"Selected source '{src.id}' did not match any occurrence in this snapshot.")
            return TraversalResult(
                lower_index=0.0,
                upper_index=0.0,
                total_scoped_weight=total_scoped_weight,
                reached_assets=[
                    ReachedAssetInfo(
                        asset_id=a.asset_id,
                        name=a.name,
                        environment=a.environment,
                        weight=scoped_weights[a.asset_id],
                        reached_in_lower=False,
                        reached_in_upper=False,
                    )
                    for a in target_assets
                ],
                witness_paths=[],
                assumptions=assumptions,
                topology_warnings=topology_warnings,
            )

        # 3. Construct Gate Resolution Map with Overrides
        edge_gate_override: Dict[str, str] = {}
        terminal_gate_override: Dict[str, str] = {}

        for override in scenario.gate_overrides:
            if override.target_type == "edge":
                edge_gate_override[override.target_id] = override.value
            elif override.target_type == "terminal":
                terminal_gate_override[override.target_id] = override.value

        # Build downstream exposure graph (reverse of consumer -> dependency)
        # In reversed graph: dependency -> consumer -> root
        rev_g = self.g.reverse(copy=True)

        # Remove cut nodes and edges
        for node in removed_nodes:
            if rev_g.has_node(node):
                rev_g.remove_node(node)

        for edge_id in cut_edges:
            # Find and remove matching edge
            edges_to_remove = []
            for u, v, data in rev_g.edges(data=True):
                if data.get("id") == edge_id:
                    edges_to_remove.append((u, v))
            for u, v in edges_to_remove:
                rev_g.remove_edge(u, v)

        # 4. Traversal for Lower and Upper sets
        # In lower set: only edges where effective gate is 'true'
        # In upper set: edges where effective gate is 'true' or 'unknown' ('false' blocks)

        def get_edge_gate(u: str, v: str, data: Dict[str, Any]) -> str:
            # In reversed graph, original edge was v -> u
            e_id = data.get("id", f"{v}->{u}")
            if e_id in edge_gate_override:
                return edge_gate_override[e_id]
            return data.get("gate_default", "unknown")

        def is_terminal_accessible(asset: AssetNode, mode: str, is_lower: bool) -> bool:
            aid = asset.asset_id
            # Check terminal override
            if aid in terminal_gate_override:
                val = terminal_gate_override[aid]
                if val == "false":
                    return False
                if is_lower and val != "true":
                    return False

            # Install-script-only mode logic:
            if mode == "install-script-only":
                # If lifecycle scripts are disabled on this asset, path is blocked
                if aid in disabled_script_assets:
                    return False
                # If terminal override explicitly blocked scripts
                if terminal_gate_override.get(f"{aid}:scripts") == "false":
                    return False

            return True

        lower_reached_assets: Set[str] = set()
        upper_reached_assets: Set[str] = set()
        witness_paths_map: Dict[str, WitnessPath] = {}

        for asset in target_assets:
            root_ref = asset.root_ref
            if not rev_g.has_node(root_ref):
                continue

            terminal_lower = is_terminal_accessible(asset, scenario.mode, is_lower=True)
            terminal_upper = is_terminal_accessible(asset, scenario.mode, is_lower=False)

            reached_lower = False
            reached_upper = False
            shortest_witness_nodes = None
            shortest_witness_edges = None

            # Test paths from any source node to root_ref
            for s_node in source_nodes:
                if not rev_g.has_node(s_node):
                    continue

                if not nx.has_path(rev_g, s_node, root_ref):
                    continue

                # Find all simple paths (bounded to avoid exponential explosion in large graphs)
                # For witness certificate, BFS / shortest path is deterministic
                try:
                    for path in nx.all_shortest_paths(rev_g, s_node, root_ref):
                        # Evaluate path gates
                        path_all_true = True
                        path_has_false = False
                        path_edges_info: List[WitnessPathEdge] = []

                        for i in range(len(path) - 1):
                            u, v = path[i], path[i + 1]
                            e_data = rev_g.get_edge_data(u, v) or {}
                            gate_val = get_edge_gate(u, v, e_data)

                            path_edges_info.append(
                                WitnessPathEdge(
                                    id=str(e_data.get("id", f"{v}->{u}")),
                                    source=v,  # Original consumer
                                    target=u,  # Original dependency
                                    gate_state=gate_val,
                                    provenance=e_data.get("provenance", "manifest"),
                                )
                            )

                            if gate_val != "true":
                                path_all_true = False
                            if gate_val == "false":
                                path_has_false = True
                                break

                        if not path_has_false and terminal_upper:
                            reached_upper = True
                            if shortest_witness_nodes is None:
                                shortest_witness_nodes = path
                                shortest_witness_edges = path_edges_info

                        if path_all_true and terminal_lower:
                            reached_lower = True
                            reached_upper = True
                            shortest_witness_nodes = path
                            shortest_witness_edges = path_edges_info
                            break

                    if reached_lower:
                        break
                except Exception:
                    continue

            if reached_lower:
                lower_reached_assets.add(asset.asset_id)
            if reached_upper:
                upper_reached_assets.add(asset.asset_id)

            if reached_upper and shortest_witness_nodes:
                witness_nodes_info = []
                for n_ref in shortest_witness_nodes:
                    node_data = rev_g.nodes.get(n_ref, {})
                    witness_nodes_info.append(
                        WitnessPathNode(
                            ref=n_ref,
                            name=node_data.get("name", n_ref),
                            version=node_data.get("version"),
                        )
                    )

                witness_paths_map[asset.asset_id] = WitnessPath(
                    asset_id=asset.asset_id,
                    asset_name=asset.name,
                    reached_in_lower=reached_lower,
                    reached_in_upper=reached_upper,
                    nodes=witness_nodes_info,
                    edges=shortest_witness_edges or [],
                )

        # 5. Calculate Weighted Exposure Indices
        lower_weight_sum = sum(scoped_weights[aid] for aid in lower_reached_assets)
        upper_weight_sum = sum(scoped_weights[aid] for aid in upper_reached_assets)

        lower_index = round((100.0 * lower_weight_sum) / total_scoped_weight, 2)
        upper_index = round((100.0 * upper_weight_sum) / total_scoped_weight, 2)

        # Invariant safety: lower cannot exceed upper
        if lower_index > upper_index:
            upper_index = lower_index

        reached_assets_info = []
        for a in target_assets:
            reached_assets_info.append(
                ReachedAssetInfo(
                    asset_id=a.asset_id,
                    name=a.name,
                    environment=a.environment,
                    weight=scoped_weights[a.asset_id],
                    reached_in_lower=(a.asset_id in lower_reached_assets),
                    reached_in_upper=(a.asset_id in upper_reached_assets),
                )
            )

        if scenario.mode == "runtime":
            assumptions.append("Mode: runtime. Evaluates execution gates; lifecycle script blocks have no effect.")
        elif scenario.mode == "install-script-only":
            assumptions.append("Mode: install-script-only. Evaluates build-time lifecycle script execution.")

        return TraversalResult(
            lower_index=lower_index,
            upper_index=upper_index,
            total_scoped_weight=total_scoped_weight,
            reached_assets=reached_assets_info,
            witness_paths=list(witness_paths_map.values()),
            assumptions=assumptions,
            topology_warnings=topology_warnings,
        )
