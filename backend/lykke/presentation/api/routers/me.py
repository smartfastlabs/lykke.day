"""Endpoints for retrieving the current authenticated user."""

from typing import Annotated

from fastapi import APIRouter, Depends
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import UserSchema
from lykke.presentation.api.schemas.mappers import map_user_to_schema

from .dependencies.user import get_current_user

router = APIRouter()


@router.get("", response_model=UserSchema)
async def get_current_user_profile(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserSchema:
    """Return the currently authenticated user."""
    return map_user_to_schema(user)
