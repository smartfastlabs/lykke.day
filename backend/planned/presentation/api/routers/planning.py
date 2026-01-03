"""Routes for planning operations."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayHandler
from planned.application.queries import PreviewDayHandler
from planned.application.queries.routine import ListRoutinesHandler
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain import value_objects
from planned.domain.entities import RoutineEntity, UserEntity
from planned.presentation.api.schemas import DayContextSchema, RoutineSchema
from planned.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_routine_to_schema,
)

from .dependencies.services import (
    get_list_routines_handler,
    get_preview_day_handler,
    get_schedule_day_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/routines", response_model=list[RoutineSchema])
async def list_routines(
    user: Annotated[UserEntity, Depends(get_current_user)],
    list_routines_handler: Annotated[
        ListRoutinesHandler, Depends(get_list_routines_handler)
    ],
) -> list[RoutineSchema]:
    """Get all routines for the current user."""
    result = await list_routines_handler.run(
        user_id=user.id,
        paginate=False,
    )
    routines = result if isinstance(result, list) else result.items
    return [map_routine_to_schema(routine) for routine in routines]


# ============================================================================
# Preview Queries
# ============================================================================


@router.get("/preview/today", response_model=DayContextSchema)
async def preview_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what today would look like if scheduled."""
    context = await handler.preview_day(user_id=user.id, date=get_current_date())
    return map_day_context_to_schema(context)


@router.get("/tomorrow/preview", response_model=DayContextSchema)
async def preview_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what tomorrow would look like if scheduled."""
    context = await handler.preview_day(user_id=user.id, date=get_tomorrows_date())
    return map_day_context_to_schema(context)


@router.get("/date/{date}/preview", response_model=DayContextSchema)
async def preview_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what a specific date would look like if scheduled."""
    context = await handler.preview_day(user_id=user.id, date=date)
    return map_day_context_to_schema(context)


# ============================================================================
# Schedule Commands
# ============================================================================


@router.put("/schedule/today", response_model=DayContextSchema)
async def schedule_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule today with tasks from routines."""
    context = await handler.schedule_day(user_id=user.id, date=get_current_date())
    return map_day_context_to_schema(context)


@router.put("/tomorrow/schedule", response_model=DayContextSchema)
async def schedule_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule tomorrow with tasks from routines."""
    context = await handler.schedule_day(user_id=user.id, date=get_tomorrows_date())
    return map_day_context_to_schema(context)


@router.put("/date/{date}/schedule", response_model=DayContextSchema)
async def schedule_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule a specific date with tasks from routines."""
    context = await handler.schedule_day(user_id=user.id, date=date)
    return map_day_context_to_schema(context)
