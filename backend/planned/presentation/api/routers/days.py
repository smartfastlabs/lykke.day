"""Routes for day operations."""

import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayCommand, UpdateDayCommand
from planned.application.mediator import Mediator
from planned.application.queries import GetDayContextQuery, PreviewDayQuery
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain import entities, value_objects
from planned.presentation.api import schemas
from planned.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_day_template_to_schema,
    map_day_to_schema,
)

from .dependencies.container import RepositoryContainer, get_repository_container
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


# ============================================================================
# Day Context Queries
# ============================================================================


@router.get("/today/context", response_model=schemas.DayContext)
async def get_context_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Get the complete context for today."""
    query = GetDayContextQuery(user=user, date=get_current_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/tomorrow/context", response_model=schemas.DayContext)
async def get_context_tomorrow(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Get the complete context for tomorrow."""
    query = GetDayContextQuery(user=user, date=get_tomorrows_date())
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/{date}/context", response_model=schemas.DayContext)
async def get_context(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Get the complete context for a specific date."""
    query = GetDayContextQuery(user=user, date=date)
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


@router.get("/{date}/preview", response_model=schemas.DayContext)
async def preview_day(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    template_id: UUID | None = None,
) -> schemas.DayContext:
    """Preview what a day would look like if scheduled."""
    query = PreviewDayQuery(user_id=user.id, date=date, template_id=template_id)
    context = await mediator.query(query)
    return map_day_context_to_schema(context)


# ============================================================================
# Day Commands
# ============================================================================


@router.put("/today/schedule", response_model=schemas.DayContext)
async def schedule_today(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayContext:
    """Schedule today with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=get_current_date())
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


@router.put("/{date}/schedule", response_model=schemas.DayContext)
async def schedule_day(
    date: datetime.date,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    template_id: UUID | None = None,
) -> schemas.DayContext:
    """Schedule a specific day with tasks from routines."""
    cmd = ScheduleDayCommand(user_id=user.id, date=date, template_id=template_id)
    context = await mediator.execute(cmd)
    return map_day_context_to_schema(context)


class UpdateDayRequest(value_objects.BaseRequestObject):
    """Request body for updating a day."""

    status: value_objects.DayStatus | None = None
    template_id: UUID | None = None


@router.patch("/{date}", response_model=schemas.Day)
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.Day:
    """Update a day's status or template."""
    cmd = UpdateDayCommand(
        user_id=user.id,
        date=date,
        status=request.status,
        template_id=request.template_id,
    )
    day = await mediator.execute(cmd)
    return map_day_to_schema(day)


# ============================================================================
# Templates (simple query via repository)
# ============================================================================


@router.get("/templates", response_model=list[schemas.DayTemplate])
async def get_templates(
    repos: Annotated[RepositoryContainer, Depends(get_repository_container)],
) -> list[schemas.DayTemplate]:
    """Get all available day templates."""
    templates = await repos.day_template_repo.all()
    return [map_day_template_to_schema(template) for template in templates]
