import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class SourceSpec(BaseModel):
    kind: Literal["occurrence", "package_identity"] = "package_identity"
    id: str  # UUID or local_ref / purl / pkg identity id
    scope: Literal["all_matching_occurrences", "single_occurrence"] = "all_matching_occurrences"


class GateOverride(BaseModel):
    target_type: Literal["edge", "terminal"] = "edge"
    target_id: str
    value: Literal["true", "false", "unknown"]
    reason: Optional[str] = None


class ScenarioCreate(BaseModel):
    snapshot_id: uuid.UUID
    source: SourceSpec
    mode: Literal["runtime", "install-script-only"] = "runtime"
    asset_ids: Optional[List[uuid.UUID]] = None
    asset_weights: Optional[Dict[str, int]] = None  # Asset ID str -> weight 1..5
    gate_overrides: List[GateOverride] = Field(default_factory=list)


class WitnessPathNode(BaseModel):
    ref: str
    name: str
    version: Optional[str] = None


class WitnessPathEdge(BaseModel):
    id: str
    source: str
    target: str
    gate_state: str
    provenance: str


class WitnessPath(BaseModel):
    asset_id: str
    asset_name: str
    reached_in_lower: bool
    reached_in_upper: bool
    nodes: List[WitnessPathNode]
    edges: List[WitnessPathEdge]
    note: Optional[str] = "Deterministic witness path; may not be exhaustive."


class ReachedAssetInfo(BaseModel):
    asset_id: str
    name: str
    environment: str
    weight: int
    reached_in_lower: bool
    reached_in_upper: bool


class RunRead(BaseModel):
    id: uuid.UUID
    snapshot_id: uuid.UUID
    scenario: ScenarioCreate
    model_version: str = "1.0.0"
    lower_index: float
    upper_index: float
    total_scoped_weight: int
    reached_assets: List[ReachedAssetInfo]
    witness_paths: List[WitnessPath]
    evidence_ids: List[uuid.UUID] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    topology_warnings: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceRead(BaseModel):
    id: uuid.UUID
    snapshot_id: uuid.UUID
    kind: str
    source_ref: Optional[str] = None
    timestamp: datetime
    trust_label: str
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
