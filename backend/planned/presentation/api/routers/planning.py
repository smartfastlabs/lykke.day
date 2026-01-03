"""Routes for planning operations."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayCommand
from planned.application.mediator import Mediator
from planned.application.queries import ListEntitiesQuery, PreviewDayQuery
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain.entities import RoutineEntity, UserEntity
from planned.presentation.api.schemas import DayContextSchema, RoutineSchema
from planned.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_routine_to_schema,
)

from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/routines", response_model=list[RoutineSchema])
async def list_routines(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> list[RoutineSchema]:
    """Get all routines for the current user."""
    query = ListEntitiesQuery[RoutineEntity](
        user_id=user.id,
        repository_name="routines",
        paginate=False,
    )
    result = await mediator.query(query)
    routines = result if isinstance(result, list) else result.items
    return [map_routine_to_schema(routine) for routine in routines]


# ============================================================================
# Preview Queries
# ============================================================================


@router.get("/preview/today", response_model=DayContextSchema)
async def preview_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Preview what today would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_current_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/tomorrow/preview", response_model=DayContextSchema)
async def preview_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Preview what tomorrow would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_tomorrows_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/date/{date}/preview", response_model=DayContextSchema)
async def preview_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Preview what a specific date would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=date)
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


# ============================================================================
# Schedule Commands
# ============================================================================


@router.put("/schedule/today", response_model=DayContextSchema)
async def schedule_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Schedule today with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_current_date())
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


@router.put("/tomorrow/schedule", response_model=DayContextSchema)
async def schedule_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Schedule tomorrow with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_tomorrows_date())
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


@router.put("/date/{date}/schedule", response_model=DayContextSchema)
async def schedule_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> DayContextSchema:
    """Schedule a specific date with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=date)
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)
