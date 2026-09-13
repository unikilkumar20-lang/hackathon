from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    app_env: str


class ReadyResponse(BaseModel):
    status: str = "ready"
    database: str
    firebase_auth_configured: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
    has_more: bool
