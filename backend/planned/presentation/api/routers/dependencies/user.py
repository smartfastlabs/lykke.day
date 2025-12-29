"""User dependency for API routes."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request

from planned.application.repositories import UserRepositoryProtocol
from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.infrastructure.repositories import UserRepository


def get_user_repo() -> UserRepositoryProtocol:
    """Get an instance of UserRepository (not user-scoped)."""
    return cast("UserRepositoryProtocol", UserRepository())


async def get_current_user(
    request: Request,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
) -> User:
    """Get the current user from the session.
    
    Args:
        request: FastAPI request object
        user_repo: UserRepository dependency (injected)
        
    Returns:
        User entity
        
    Raises:
        AuthorizationError: If user is not authenticated
    """
    # Get user_uuid from session
    user_uuid_str = request.session.get("user_uuid")
    
    if not user_uuid_str:
        # Fallback to logged_in_at for backward compatibility during migration
        logged_in_at = request.session.get("logged_in_at")
        if not logged_in_at:
            raise exceptions.AuthorizationError(
                "Not authenticated. Please log in.",
            )
        # If only logged_in_at exists, we can't determine which user
        # This should only happen during migration
        raise exceptions.AuthorizationError(
            "Session invalid. Please log in again.",
        )
    
    # Convert string to UUID and get user
    try:
        user_uuid = UUID(user_uuid_str)
    except (ValueError, TypeError):
        raise exceptions.AuthorizationError(
            "Invalid session data. Please log in again.",
        )
    
    try:
        user = await user_repo.get(user_uuid)
    except exceptions.NotFoundError:
        raise exceptions.AuthorizationError(
            "User not found. Please log in again.",
        )
    
    return user



