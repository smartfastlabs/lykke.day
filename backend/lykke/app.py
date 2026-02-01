import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from redis import asyncio as aioredis  # type: ignore

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
from lykke.presentation.api.routers import auth_sms, router
from lykke.presentation.handler_factory import build_domain_event_handler
from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
from lykke.presentation.workers.tasks.registry import WorkerRegistry


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
    # Create Redis connection pool for shared use across all gateway instances
    redis_pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        encoding="utf-8",
        decode_responses=False,  # We'll handle decoding manually
    )
    logger.info(
        f"Created Redis connection pool (max_connections={settings.REDIS_MAX_CONNECTIONS})"
    )

    # Store the pool in app state for dependency injection
    fastapi_app.state.redis_pool = redis_pool

    # Initialize Redis PubSub gateway with shared connection pool
    pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)

    # Auto-register all domain event handlers
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    uow_factory = SqlAlchemyUnitOfWorkFactory(
        pubsub_gateway=pubsub_gateway,
        workers_to_schedule_factory=lambda: WorkersToSchedule(WorkerRegistry()),
    )
    register_all_handlers(
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        handler_factory=build_domain_event_handler,
    )
    from lykke.application.events.handlers.base import DomainEventHandler

    logger.info(
        f"Registered {len(DomainEventHandler._handler_classes)} domain event handler class(es)"
    )

    yield  # type: ignore

    # Clean up Redis connection pool on shutdown
    await pubsub_gateway.close()
    # Disconnect all connections in the pool
    redis_pool.disconnect()
    logger.info("Closed Redis connection pool")

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

# Reset-password router removed; use SMS login flow instead

# SMS code auth (phone-only signup/login)
app.include_router(
    auth_sms.router,
    prefix=f"{settings.API_PREFIX}/auth/sms",
    tags=["auth", "sms"],
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
