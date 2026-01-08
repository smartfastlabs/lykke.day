"""Endpoints for retrieving the current authenticated user."""

from typing import Annotated

from fastapi import APIRouter, Depends
from lykke.application.commands.user import UpdateUserHandler
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserSetting, UserUpdateObject
from lykke.presentation.api.schemas import UserSchema, UserUpdateSchema
from lykke.presentation.api.schemas.mappers import map_user_to_schema

from .dependencies.commands.user import get_update_user_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("", response_model=UserSchema)
async def get_current_user_profile(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserSchema:
    """Return the currently authenticated user."""
    return map_user_to_schema(user)


@router.put("", response_model=UserSchema)
async def update_current_user_profile(
    update_data: UserUpdateSchema,
    update_user_handler: Annotated[
        UpdateUserHandler, Depends(get_update_user_handler)
    ],
) -> UserSchema:
    """Update the current authenticated user."""
    settings = (
        UserSetting(template_defaults=update_data.settings.template_defaults)
        if update_data.settings and update_data.settings.template_defaults is not None
        else None
    )

    update_object = UserUpdateObject(
        phone_number=update_data.phone_number,
        status=update_data.status,
        is_active=update_data.is_active,
        is_superuser=update_data.is_superuser,
        is_verified=update_data.is_verified,
        settings=settings,
    )
    updated_user = await update_user_handler.run(update_data=update_object)
    return map_user_to_schema(updated_user)
