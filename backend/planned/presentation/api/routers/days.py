"""Routes for day operations."""

import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayCommand, UpdateDayCommand
from planned.application.mediator import Mediator
from planned.application.queries import GetDayContextQuery, PreviewDayQuery
from planned.domain import entities, value_objects
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from .dependencies.container import RepositoryContainer, get_repository_container
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


# ============================================================================
# Day Context Queries
# ============================================================================


@router.get("/today/context")
async def get_context_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> value_objects.DayContext:
    """Get the complete context for today."""
    query = GetDayContextQuery(user=user, date=get_current_date())
    return await mediator.query(query)


@router.get("/tomorrow/context")
async def get_context_tomorrow(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> value_objects.DayContext:
    """Get the complete context for tomorrow."""
    query = GetDayContextQuery(user=user, date=get_tomorrows_date())
    return await mediator.query(query)


@router.get("/{date}/context")
async def get_context(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> value_objects.DayContext:
    """Get the complete context for a specific date."""
    query = GetDayContextQuery(user=user, date=date)
    return await mediator.query(query)


@router.get("/{date}/preview")
async def preview_day(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    template_id: UUID | None = None,
) -> value_objects.DayContext:
    """Preview what a day would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=date, template_id=template_id)
    return await mediator.query(query)


# ============================================================================
# Day Commands
# ============================================================================


@router.put("/today/schedule")
async def schedule_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> value_objects.DayContext:
    """Schedule today with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_current_date())
    return await mediator.execute(cmd)


@router.put("/{date}/schedule")
async def schedule_day(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    template_id: UUID | None = None,
) -> value_objects.DayContext:
    """Schedule a specific day with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=date, template_id=template_id)
    return await mediator.execute(cmd)


class UpdateDayRequest(value_objects.BaseRequestObject):
    """Request body for updating a day."""

    status: value_objects.DayStatus | None = None
    template_id: UUID | None = None


@router.patch("/{date}")
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.Day:
    """Update a day's status or template."""
    cmd = UpdateDayCommand(
        user_id=user.id,
        date=date,
        status=request.status,
        template_id=request.template_id,
    )
    return await mediator.execute(cmd)


# ============================================================================
# Templates (simple query via repository)
# ============================================================================


@router.get("/templates")
async def get_templates(
    repos: Annotated[RepositoryContainer, Depends(get_repository_container)],
) -> list[entities.DayTemplate]:
    """Get all available day templates."""
    return await repos.day_template_repo.all()
