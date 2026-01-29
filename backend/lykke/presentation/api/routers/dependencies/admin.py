"""Admin dependencies for API routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from loguru import logger

from lykke.core.exceptions import AuthenticationError
from lykke.domain.entities import UserEntity

from .user import get_current_user, get_current_user_from_token


async def get_current_superuser(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserEntity:
    """Get the current user and verify they are a superuser.

    Args:
        user: Current authenticated user

    Returns:
        User entity if superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return user


async def get_current_superuser_from_token(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
) -> UserEntity:
    """Authenticate superuser from WebSocket connection.

    Uses get_current_user_from_token dependency to authenticate,
    then verifies the user is a superuser.

    Args:
        user: Authenticated user from WebSocket token

    Returns:
        Authenticated superuser entity

    Raises:
        AuthenticationError: If user is not superuser
    """
    logger.info(f"get_current_superuser_from_token: user={user.id}, is_superuser={user.is_superuser}")
    if not user.is_superuser:
        logger.warning(f"User {user.id} is not a superuser")
        raise AuthenticationError("Superuser access required")
    return user
