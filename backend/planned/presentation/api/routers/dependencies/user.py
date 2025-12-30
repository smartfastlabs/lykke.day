"""User dependency for API routes."""

from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import Depends
from planned.domain.entities import User as UserEntity
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.auth import current_active_user
from planned.infrastructure.database.tables import User as UserDB


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
    settings = UserSetting(**settings_data) if settings_data else UserSetting()

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
