import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from lykke.application.events import register_all_handlers
from lykke.core.config import settings
from lykke.core.exceptions import BaseError
from lykke.core.observability import init_sentry_fastapi
from lykke.core.utils import youtube
from lykke.infrastructure.auth import UserCreate, UserRead, auth_backend, fastapi_users
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.presentation.api.routers import router


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
    # Initialize Redis PubSub gateway for real-time event broadcasting
    pubsub_gateway = RedisPubSubGateway()

    # Auto-register all domain event handlers
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)
    register_all_handlers(
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    from lykke.application.events.handlers.base import DomainEventHandler

    logger.info(
        f"Registered {len(DomainEventHandler._handler_classes)} domain event handler class(es)"
    )

    yield  # type: ignore

    # Clean up Redis connection on shutdown
    await pubsub_gateway.close()

    if not is_testing():
        youtube.kill_current_player()


app = FastAPI(
    title="Lykke.day",
    description="API for managing calendar events",
    debug=settings.DEBUG,
    lifespan=init_lifespan,
    redirect_slashes=False,
)

init_sentry_fastapi(app)


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
        "https://lykke.day",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
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

app.include_router(
    fastapi_users.get_reset_password_router(),
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
