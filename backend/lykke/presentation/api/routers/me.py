"""Endpoints for retrieving the current authenticated user."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.application.queries import GetDayContextHandler, GetDayContextQuery
from lykke.application.commands.day import (
    AddGoalToDayCommand,
    AddGoalToDayHandler,
    RemoveGoalCommand,
    RemoveGoalHandler,
    UpdateGoalStatusCommand,
    UpdateGoalStatusHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserSetting, UserUpdateObject
from lykke.presentation.api.schemas import (
    UserSchema,
    UserUpdateSchema,
    DayContextSchema,
)
from lykke.presentation.api.schemas.mappers import map_user_to_schema, map_day_context_to_schema
from lykke.core.utils.dates import get_current_date

from .dependencies.factories import get_command_handler
from .dependencies.user import get_current_user
from .dependencies.services import (
    day_context_handler,
    get_add_goal_to_day_handler,
    get_remove_goal_handler,
    get_update_goal_status_handler,
)

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
        UpdateUserHandler, Depends(get_command_handler(UpdateUserHandler))
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
    updated_user = await update_user_handler.handle(UpdateUserCommand(update_data=update_object))
    return map_user_to_schema(updated_user)


# ============================================================================
# Today's Goals
# ============================================================================


@router.post("/today/goals", response_model=DayContextSchema)
async def add_goal_to_today(
    name: str,
    handler: Annotated[AddGoalToDayHandler, Depends(get_add_goal_to_day_handler)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Add a goal to today."""
    date = get_current_date()
    await handler.handle(AddGoalToDayCommand(date=date, goal=name))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context)


@router.patch("/today/goals/{goal_id}", response_model=DayContextSchema)
async def update_today_goal_status(
    goal_id: UUID,
    status: value_objects.GoalStatus,
    handler: Annotated[
        UpdateGoalStatusHandler, Depends(get_update_goal_status_handler)
    ],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Update a goal's status for today."""
    date = get_current_date()
    completed = status == value_objects.GoalStatus.COMPLETE
    await handler.handle(UpdateGoalStatusCommand(date=date, goal_id=goal_id, completed=completed))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context)


@router.delete("/today/goals/{goal_id}", response_model=DayContextSchema)
async def remove_goal_from_today(
    goal_id: UUID,
    handler: Annotated[RemoveGoalHandler, Depends(get_remove_goal_handler)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Remove a goal from today."""
    date = get_current_date()
    await handler.handle(RemoveGoalCommand(date=date, goal_id=goal_id))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context)
