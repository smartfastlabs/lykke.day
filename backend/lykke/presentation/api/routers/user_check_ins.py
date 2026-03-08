"""Router for user check-ins (authenticated /me scope)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from lykke.application.commands.user_check_in import (
    CreateUserCheckInCommand,
    CreateUserCheckInHandler,
)
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import UserCheckInCreateSchema, UserCheckInSchema
from lykke.presentation.api.schemas.mappers import map_user_check_in_to_schema

from .dependencies.factories import create_command_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.post(
    "/",
    response_model=UserCheckInSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_check_in(
    data: UserCheckInCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        CreateUserCheckInHandler,
        Depends(create_command_handler(CreateUserCheckInHandler)),
    ],
) -> UserCheckInSchema:
    """Create a user-authored check-in (scores and/or free-form text)."""
    created = await handler.handle(
        CreateUserCheckInCommand(
            text=data.text,
            scores=data.scores,
            checkin_at=data.checkin_at,
        )
    )
    return map_user_check_in_to_schema(created)
