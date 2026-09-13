import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.db.session import Base, engine
from app.db import models  # noqa: F401
from app.api.v1 import (
    health,
    auth,
    projects,
    snapshots,
    runs,
    optimizations,
    enrichment,
    demo,
)
from app import web_console

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rippleguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
    except Exception as e:
        logger.warning(f"Could not auto-create tables on startup: {e}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Explainable open-source dependency risk analysis and compromise-scenario simulation API.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and Timing Middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            return response
        except AppException as exc:
            return await app_exception_handler(request, exc)
        except RequestValidationError as exc:
            return await validation_exception_handler(request, exc)
        except Exception as exc:
            logger.exception(f"Unhandled exception during request: {exc}")
            return await generic_exception_handler(request, exc)

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # API v1 Router with prefix
    api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
    api_v1_router.include_router(health.router)
    api_v1_router.include_router(auth.router)
    api_v1_router.include_router(projects.router)
    api_v1_router.include_router(snapshots.router)
    api_v1_router.include_router(runs.router)
    api_v1_router.include_router(optimizations.router)
    api_v1_router.include_router(enrichment.router)
    api_v1_router.include_router(demo.router)

    app.include_router(api_v1_router)
    
    # Also mount health router, demo router, and web console directly at root level
    app.include_router(health.router)
    app.include_router(demo.router)
    app.include_router(web_console.router)

    return app


app = create_app()
