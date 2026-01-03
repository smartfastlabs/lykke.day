import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from planned.application.events import register_all_handlers
from planned.core.config import settings
from planned.core.exceptions import BaseError
from planned.infrastructure.auth import (
    UserCreate,
    UserRead,
    auth_backend,
    fastapi_users,
)
from planned.core.utils import youtube
from planned.presentation.api.routers import router

# Keep references to event handlers to prevent garbage collection
_event_handlers: list = []


def is_testing() -> bool:
    """Check if the application is running in a test environment."""
    return "pytest" in sys.modules or os.getenv("ENV_FILE", "").endswith(".test")


logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
)


@asynccontextmanager
async def init_lifespan(fastapi_app: FastAPI) -> AsyncIterator[Never]:
    """
    Lifespan context manager for FastAPI application.
    """
    # Auto-register all domain event handlers
    _event_handlers.extend(register_all_handlers())
    logger.info(f"Registered {len(_event_handlers)} domain event handler(s)")

    yield  # type: ignore

    if not is_testing():
        youtube.kill_current_player()


app = FastAPI(
    title="Planned.day",
    description="API for managing calendar events",
    debug=settings.DEBUG,
    lifespan=init_lifespan,
)


# Set all CORS enabled origins
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [
        "planned.day",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Include FastAPI Users auth routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["auth"],
)

# Include application router
app.include_router(
    router,
    prefix=settings.API_PREFIX,
)


@app.exception_handler(BaseError)
async def custom_exception_handler(_request: Request, exc: BaseError) -> JSONResponse:
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {"status": "healthy"}
