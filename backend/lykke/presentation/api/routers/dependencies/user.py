"""User dependency for API routes."""

from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import Depends, WebSocket
from fastapi_users.exceptions import UserNotExists
from lykke.core.exceptions import AuthenticationError
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.infrastructure.auth import current_active_user, get_jwt_strategy, get_user_db
from lykke.infrastructure.database.tables import User as UserDB


async def get_current_user(
    user: Annotated[UserDB, Depends(current_active_user)],
) -> UserEntity:
    """Get the current user from fastapi-users and convert to domain entity.

    Args:
        user: SQLAlchemy User model from fastapi-users

    Returns:
        User domain entity
    """
    # Parse settings from JSONB
    settings_data = cast("dict[str, Any] | None", user.settings)
    settings = value_objects.UserSetting(**settings_data) if settings_data else value_objects.UserSetting()

    # Convert SQLAlchemy model to domain entity
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


def _db_user_to_entity(user: UserDB) -> UserEntity:
    """Convert SQLAlchemy User model to domain entity.
    
    Args:
        user: SQLAlchemy User model
        
    Returns:
        User domain entity
    """
    settings_data = cast("dict[str, Any] | None", user.settings)
    settings = value_objects.UserSetting(**settings_data) if settings_data else value_objects.UserSetting()
    
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
        jwt_strategy = get_jwt_strategy()
        # Pass None for user_manager since we only need to decode the token
        user_id_str = await jwt_strategy.read_token(token, user_manager=None)  # type: ignore[arg-type]

        if user_id_str is None:
            raise AuthenticationError("Invalid authentication token")

        # Get user from database using the generator pattern
        from lykke.infrastructure.auth import get_async_session

        async for session in get_async_session():
            async for user_db in get_user_db(session):
                user = await user_db.get(user_id_str)

                if user is None:
                    raise UserNotExists()

                if not user.is_active:
                    raise AuthenticationError("User is not active")

                # Convert to domain entity
                return _db_user_to_entity(user)

        raise AuthenticationError("Failed to get database session")

    except UserNotExists:
        raise AuthenticationError("User not found")
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}")
