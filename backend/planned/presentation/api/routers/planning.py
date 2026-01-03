"""Routes for planning operations."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.commands import ScheduleDayCommand
from planned.application.mediator import Mediator
from planned.application.queries import PreviewDayQuery
from planned.application.repositories import RoutineRepositoryProtocol
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain import value_objects
from planned.domain.entities import UserEntity
from planned.presentation.api import schemas
from planned.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_routine_to_schema,
)

from .dependencies.repositories import get_routine_repo
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/routines", response_model=list[schemas.Routine])
async def list_routines(
    routine_repo: Annotated[RoutineRepositoryProtocol, Depends(get_routine_repo)],
) -> list[schemas.Routine]:
    """Get all routines for the current user."""
    routines = await routine_repo.all()
    return [map_routine_to_schema(routine) for routine in routines]


# ============================================================================
# Preview Queries
# ============================================================================


@router.get("/preview/today", response_model=schemas.DayContext)
async def preview_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Preview what today would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_current_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/tomorrow/preview", response_model=schemas.DayContext)
async def preview_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Preview what tomorrow would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_tomorrows_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/date/{date}/preview", response_model=schemas.DayContext)
async def preview_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Preview what a specific date would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=date)
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


# ============================================================================
# Schedule Commands
# ============================================================================


@router.put("/schedule/today", response_model=schemas.DayContext)
async def schedule_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Schedule today with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_current_date())
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


@router.put("/tomorrow/schedule", response_model=schemas.DayContext)
async def schedule_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Schedule tomorrow with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_tomorrows_date())
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


@router.put("/date/{date}/schedule", response_model=schemas.DayContext)
async def schedule_date(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Schedule a specific date with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=date)
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)
