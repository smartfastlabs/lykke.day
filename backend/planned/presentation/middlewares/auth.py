from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from planned.core.exceptions import exceptions


def mock_for_testing() -> bool:
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks if the user is authenticated by verifying
    """

    def __init__(
        self,
        app: FastAPI,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        # Paths that don't require authentication
        self.exclude_paths = exclude_paths or [
            "/auth/set-password",
            "/auth/login",
            "/auth/register",
            "/api/auth/set-password",
            "/api/auth/login",
            "/api/auth/register",
            "/health",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if mock_for_testing():
            return await call_next(request)

        # Skip auth check for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check if session exists
        if not hasattr(request, "session"):
            raise exceptions.ServerError(
                "Session middleware not configured",
            )

        user_uuid = request.session.get("user_uuid")
        if user_uuid:
            # Validate that user_uuid is a valid UUID string
            try:
                UUID(user_uuid)  # Validate format
            except (ValueError, TypeError):
                raise exceptions.AuthorizationError(
                    "Invalid session data. Please log in again.",
                )
        else:
            raise exceptions.AuthorizationError(
                "Not authenticated. Please log in.",
            )

        return await call_next(request)
