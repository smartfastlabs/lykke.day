"""Routes for planning operations."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayCommand
from planned.application.mediator import Mediator
from planned.application.queries import PreviewDayQuery
from planned.application.repositories import RoutineRepositoryProtocol
from planned.domain import entities
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from .dependencies.repositories import get_routine_repo
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/routines")
async def list_routines(
    routine_repo: Annotated[RoutineRepositoryProtocol, Depends(get_routine_repo)],
) -> list[entities.Routine]:
    """Get all routines for the current user."""
    return await routine_repo.all()


# ============================================================================
# Preview Queries
# ============================================================================


@router.get("/preview/today")
async def preview_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Preview what today would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_current_date())
    return await mediator.query(query)


@router.get("/tomorrow/preview")
async def preview_tomorrow(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Preview what tomorrow would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=get_tomorrows_date())
    return await mediator.query(query)


@router.get("/date/{date}/preview")
async def preview_date(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Preview what a specific date would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=date)
    return await mediator.query(query)


# ============================================================================
# Schedule Commands
# ============================================================================


@router.put("/schedule/today")
async def schedule_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Schedule today with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_current_date())
    return await mediator.execute(cmd)


@router.put("/tomorrow/schedule")
async def schedule_tomorrow(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Schedule tomorrow with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_tomorrows_date())
    return await mediator.execute(cmd)


@router.put("/date/{date}/schedule")
async def schedule_date(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.DayContext:
    """Schedule a specific date with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=date)
    return await mediator.execute(cmd)
