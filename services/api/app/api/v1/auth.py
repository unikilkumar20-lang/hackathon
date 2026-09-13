from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.db.models import User
from app.schemas.user import UserRead

router = APIRouter(tags=["Auth"])


@router.get("/me", response_model=UserRead)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated Firebase user profile."""
    return current_user
