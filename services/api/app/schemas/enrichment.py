import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class AdvisoryRead(BaseModel):
    id: uuid.UUID
    provider: str
    external_id: str
    aliases: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime

    model_config = {"from_attributes": True}


class FindingRead(BaseModel):
    id: uuid.UUID
    check_id: uuid.UUID
    package_identity_id: uuid.UUID
    package_name: str
    package_version: str
    ecosystem: str
    canonical_purl: Optional[str] = None
    advisory: AdvisoryRead
    match_details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class EnrichmentCheckRead(BaseModel):
    id: uuid.UUID
    snapshot_id: uuid.UUID
    provider: str = "osv"
    status: Literal["pending", "complete", "partial", "failed"]
    coverage: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    findings_count: int = 0

    model_config = {"from_attributes": True}
