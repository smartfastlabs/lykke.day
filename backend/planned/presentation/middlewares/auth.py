from collections.abc import Awaitable, Callable
from datetime import datetime

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from planned.core.exceptions import exceptions


def mock_for_testing() -> bool:
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks if the user is authenticated by verifying
    the presence of a valid 'logged_in_at' datetime in the session.
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

        # Check for user_uuid in session (primary check)
        user_uuid = request.session.get("user_uuid")
        
        # Fallback to logged_in_at for backward compatibility during migration
        logged_in_at = request.session.get("logged_in_at")
        
        # Check if user_uuid exists (preferred)
        if user_uuid:
            # Validate that user_uuid is a valid UUID string
            try:
                from uuid import UUID
                UUID(user_uuid)  # Validate format
            except (ValueError, TypeError):
                raise exceptions.AuthorizationError(
                    "Invalid session data. Please log in again.",
                )
        elif logged_in_at:
            # Backward compatibility: validate logged_in_at
            try:
                if isinstance(logged_in_at, str):
                    datetime.fromisoformat(logged_in_at)
                else:
                    raise exceptions.AuthorizationError("Invalid datetime format")
            except (ValueError, TypeError) as e:
                raise exceptions.AuthorizationError(
                    "Invalid session data. Please log in again.",
                ) from e
        else:
            # Neither user_uuid nor logged_in_at exists
            raise exceptions.AuthorizationError(
                "Not authenticated. Please log in.",
            )

        return await call_next(request)
