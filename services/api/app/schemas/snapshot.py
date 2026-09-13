import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SnapshotCreate(BaseModel):
    asset_id: Optional[uuid.UUID] = None
    source_type: str = "cyclonedx-json"
    root_ref: Optional[str] = None


class SnapshotRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    content_hash: str
    parser_version: str
    topology_status: str
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime
    occurrence_count: int = 0
    edge_count: int = 0
    inventory_count: int = 0

    model_config = {"from_attributes": True}


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str  # "root", "asset", "occurrence"
    name: str
    version: Optional[str] = None
    ecosystem: Optional[str] = None
    purl: Optional[str] = None
    asset_id: Optional[uuid.UUID] = None
    environment: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str  # consumer occurrence or root
    target: str  # dependency occurrence
    gate_default: str = "unknown"  # true, false, unknown
    context: Dict[str, Any] = Field(default_factory=dict)
    provenance: str = "cyclonedx-manifest"


class GraphResponse(BaseModel):
    snapshot_id: uuid.UUID
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    is_truncated: bool = False
    total_nodes: int
    total_edges: int
    topology_status: str
    warnings: List[str] = Field(default_factory=list)
