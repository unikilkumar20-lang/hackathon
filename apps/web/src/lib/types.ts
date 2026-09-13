export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface Asset {
  id: string;
  project_id: string;
  name: string;
  environment: string;
  default_weight: number;
  created_at: string;
}

export interface Project {
  id: string;
  owner_user_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  asset_count: number;
  snapshot_count: number;
  assets?: Asset[];
}

export interface Snapshot {
  id: string;
  project_id: string;
  content_hash: string;
  parser_version: string;
  topology_status: "complete" | "incomplete" | "degraded";
  warnings: string[];
  created_at: string;
  occurrence_count: number;
  edge_count: number;
  inventory_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  kind: "root" | "asset" | "occurrence";
  name: string;
  version?: string | null;
  ecosystem?: string | null;
  purl?: string | null;
  asset_id?: string | null;
  environment?: string | null;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  gate_default: "true" | "false" | "unknown";
  context?: Record<string, unknown>;
  provenance: string;
}

export interface GraphResponse {
  snapshot_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  is_truncated: boolean;
  total_nodes: number;
  total_edges: number;
  topology_status: string;
  warnings: string[];
}

export interface ReachedAssetInfo {
  asset_id: string;
  name: string;
  environment: string;
  weight: number;
  reached_in_lower: boolean;
  reached_in_upper: boolean;
}

export interface WitnessPathNode {
  ref: string;
  name: string;
  version?: string | null;
}

export interface WitnessPathEdge {
  id: string;
  source: string;
  target: string;
  gate_state: string;
  provenance: string;
}

export interface WitnessPath {
  asset_id: string;
  asset_name: string;
  reached_in_lower: boolean;
  reached_in_upper: boolean;
  nodes: WitnessPathNode[];
  edges: WitnessPathEdge[];
  note?: string;
}

export interface Run {
  id: string;
  snapshot_id: string;
  model_version: string;
  lower_index: number;
  upper_index: number;
  total_scoped_weight: number;
  reached_assets: ReachedAssetInfo[];
  witness_paths: WitnessPath[];
  evidence_ids: string[];
  assumptions: string[];
  topology_warnings: string[];
  created_at: string;
}

export interface CandidateControl {
  id: string;
  label: string;
  cost: number;
  control_type:
    | "disable_lifecycle_scripts"
    | "exclude_dependency_route"
    | "replace_occurrence"
    | "remove_package_version";
  parameters: Record<string, unknown>;
  mechanism_scope: string;
  assumptions?: string[];
}

export interface OptimizationResult {
  id: string;
  run_id: string;
  budget: number;
  candidate_set_hash: string;
  chosen_controls: CandidateControl[];
  total_cost: number;
  baseline_lower: number;
  baseline_upper: number;
  optimized_lower: number;
  optimized_upper: number;
  absolute_reduction: number;
  relative_reduction: number | null;
  residual_assets: ReachedAssetInfo[];
  residual_paths: WitnessPath[];
  assumptions: string[];
  side_effects: string[];
  optimizer_version: string;
  created_at: string;
}
