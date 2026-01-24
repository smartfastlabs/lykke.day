"""User dependency for API routes."""

from typing import TYPE_CHECKING, Annotated, Any, cast
from uuid import UUID

from fastapi import Depends, Request, WebSocket
from fastapi_users.exceptions import UserNotExists

from lykke.core.exceptions import AuthenticationError
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.infrastructure.auth import current_active_user, get_jwt_strategy, get_user_db
from lykke.infrastructure.database.tables import User as UserDB

if TYPE_CHECKING:
    from datetime import datetime


def _db_user_to_entity(user: UserDB) -> UserEntity:
    """Convert SQLAlchemy User model to domain entity.

    Args:
        user: SQLAlchemy User model

    Returns:
        User domain entity
    """
    settings_data = cast("dict[str, Any] | None", user.settings)
    settings = (
        value_objects.UserSetting(**settings_data)
        if settings_data
        else value_objects.UserSetting()
    )

    return UserEntity(
        id=user.id,
        email=user.email,
        phone_number=cast("str | None", user.phone_number),
        hashed_password=user.hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        settings=settings,
        created_at=cast("datetime", user.created_at),
        updated_at=cast("datetime | None", user.updated_at),
    )


async def get_current_user(
    user: Annotated[UserDB, Depends(current_active_user)],
) -> UserEntity:
    """Get the current user from fastapi-users and convert to domain entity.

    Works for HTTP requests using FastAPI Users authentication.

    Args:
        user: SQLAlchemy User model from fastapi-users

    Returns:
        User domain entity
    """
    return _db_user_to_entity(user)


async def get_current_user_from_token(websocket: WebSocket) -> UserEntity:
    """Authenticate user from WebSocket connection.

    Extracts JWT token from cookies or query parameters and validates it.

    Args:
        websocket: WebSocket connection

    Returns:
        Authenticated user entity

    Raises:
        AuthenticationError: If authentication fails
    """
    # Try to get token from cookie first
    token = websocket.cookies.get("lykke_auth")

    # Fallback to query parameter for non-browser clients
    if not token:
        token = websocket.query_params.get("token")

    if not token:
        raise AuthenticationError("Authentication token not provided")

    try:
        # Decode JWT token
        # We need to create a user_manager to parse the token
        from lykke.infrastructure.auth import (
            get_async_session,
            get_user_db,
            get_user_manager,
        )

        async for session in get_async_session():
            async for user_db in get_user_db(session):
                async for user_manager in get_user_manager(user_db):
                    jwt_strategy = get_jwt_strategy()
                    result: Any = await jwt_strategy.read_token(
                        token, user_manager=user_manager
                    )

                    if result is None:
                        raise AuthenticationError("Invalid authentication token")

                    # read_token can return either a user object or a user ID string
                    # Check if it's already a user object
                    from lykke.infrastructure.database.tables import User as UserDB

                    if isinstance(result, UserDB):
                        user = result
                    elif isinstance(result, (str, UUID)):
                        # It's a user ID (string or UUID), fetch the user
                        user_id = UUID(result) if isinstance(result, str) else result
                        fetched_user = await user_db.get(user_id)
                        if fetched_user is None:
                            raise UserNotExists()
                        user = fetched_user
                    else:
                        raise AuthenticationError("Invalid token result type")

                    if not user.is_active:
                        raise AuthenticationError("User is not active")

                    # Convert to domain entity
                    return _db_user_to_entity(user)

        raise AuthenticationError("Failed to get database session")

    except UserNotExists as e:
        raise AuthenticationError("User not found") from e
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {e!s}") from e
