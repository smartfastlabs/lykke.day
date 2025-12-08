from collections.abc import Awaitable, Callable
from datetime import datetime

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from planned import exceptions


def mock_for_testing() -> bool:
    return True
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

        # Get logged_in_at from session
        logged_in_at = request.session.get("logged_in_at")

        # Check if logged_in_at exists
        if not logged_in_at:
            raise exceptions.AuthorizationError(
                "Not authenticated. Please log in.",
            )

        # Validate that logged_in_at is a valid datetime
        try:
            # If it's stored as a string (common in sessions), parse it
            if isinstance(logged_in_at, str):
                datetime.fromisoformat(logged_in_at)
            else:
                raise exceptions.AuthorizationError("Invalid datetime format")
        except (ValueError, TypeError) as e:
            raise exceptions.AuthorizationError(
                "Invalid session data. Please log in again.",
            ) from e

        return await call_next(request)
