from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe. Does not expose secrets."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        app_env=settings.APP_ENV,
    )


@router.get("/ready", response_model=ReadyResponse)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe. Checks database connectivity and sanitized status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:50]}"

    firebase_configured = bool(
        settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_PROJECT_ID != "replace_me"
    )

    return ReadyResponse(
        status="ready" if db_status == "connected" else "degraded",
        database=db_status,
        firebase_auth_configured=firebase_configured,
    )
