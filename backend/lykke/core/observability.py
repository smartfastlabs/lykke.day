"""Observability utilities such as Sentry initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.starlette import StarletteIntegration

from lykke.core.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def init_sentry_fastapi(app: Any) -> None:
    """Initialize Sentry for the FastAPI application."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[StarletteIntegration()],
    )

    app.add_middleware(SentryAsgiMiddleware)


def init_sentry_taskiq() -> None:
    """Initialize Sentry for Taskiq workers."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )
