import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    firebase_uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
