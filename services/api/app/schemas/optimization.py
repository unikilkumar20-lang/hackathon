import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from app.schemas.run import ReachedAssetInfo, WitnessPath


class CandidateControl(BaseModel):
    id: str
    label: str
    cost: int = Field(ge=1, description="Effort units (positive integer)")
    control_type: Literal[
        "disable_lifecycle_scripts",
        "exclude_dependency_route",
        "replace_occurrence",
        "remove_package_version",
    ]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    mechanism_scope: str = "environment"
    assumptions: List[str] = Field(default_factory=list)


class OptimizationRequest(BaseModel):
    budget: int = Field(ge=0, description="Available effort budget")
    candidate_controls: List[CandidateControl] = Field(
        ..., min_length=1, max_length=8, description="Between 1 and 8 candidate controls"
    )


class OptimizationRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    budget: int
    candidate_set_hash: str
    chosen_controls: List[CandidateControl]
    total_cost: int
    baseline_lower: float
    baseline_upper: float
    optimized_lower: float
    optimized_upper: float
    absolute_reduction: float
    relative_reduction: Optional[float] = None  # None if baseline_upper == 0
    residual_assets: List[ReachedAssetInfo]
    residual_paths: List[WitnessPath]
    assumptions: List[str] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    optimizer_version: str = "1.0.0"
    created_at: datetime

    model_config = {"from_attributes": True}
