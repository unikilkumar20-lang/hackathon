import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Asset or service name")
    environment: str = Field(default="production", max_length=64, description="Environment name e.g. production, staging")
    default_weight: int = Field(default=3, ge=1, le=5, description="User-assigned business importance weight (1 to 5)")


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    environment: Optional[str] = Field(None, max_length=64)
    default_weight: Optional[int] = Field(None, ge=1, le=5)


class AssetRead(AssetBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
