"""Routes for day operations."""

import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from planned.application.commands import ScheduleDayHandler, UpdateDayHandler
from planned.application.queries import GetDayContextHandler, PreviewDayHandler
from planned.application.queries.day_template import ListDayTemplatesHandler
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain import value_objects
from planned.domain.entities import DayTemplateEntity, UserEntity
from planned.presentation.api.schemas import (
    DayContextSchema,
    DaySchema,
    DayTemplateSchema,
)
from planned.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_day_template_to_schema,
    map_day_to_schema,
)
from pydantic import BaseModel

from .dependencies.queries.day_template import get_list_day_templates_handler
from .dependencies.services import (
    get_get_day_context_handler,
    get_preview_day_handler,
    get_schedule_day_handler,
    get_update_day_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


# ============================================================================
# Day Context Queries
# ============================================================================


@router.get("/today/context", response_model=DayContextSchema)
async def get_context_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetDayContextHandler, Depends(get_get_day_context_handler)],
) -> DayContextSchema:
    """Get the complete context for today."""
    context = await handler.get_day_context(user=user, date=get_current_date())
    return map_day_context_to_schema(context)


@router.get("/tomorrow/context", response_model=DayContextSchema)
async def get_context_tomorrow(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetDayContextHandler, Depends(get_get_day_context_handler)],
) -> DayContextSchema:
    """Get the complete context for tomorrow."""
    context = await handler.get_day_context(user=user, date=get_tomorrows_date())
    return map_day_context_to_schema(context)


@router.get("/{date}/context", response_model=DayContextSchema)
async def get_context(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetDayContextHandler, Depends(get_get_day_context_handler)],
) -> DayContextSchema:
    """Get the complete context for a specific date."""
    context = await handler.get_day_context(user=user, date=date)
    return map_day_context_to_schema(context)


@router.get("/{date}/preview", response_model=DayContextSchema)
async def preview_day(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
    template_id: UUID | None = None,
) -> DayContextSchema:
    """Preview what a day would look like if scheduled."""
    context = await handler.preview_day(
        user_id=user.id, date=date, template_id=template_id
    )
    return map_day_context_to_schema(context)


# ============================================================================
# Day Commands
# ============================================================================


@router.put("/today/schedule", response_model=DayContextSchema)
async def schedule_today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule today with tasks from routines."""
    context = await handler.schedule_day(user_id=user.id, date=get_current_date())
    return map_day_context_to_schema(context)


@router.put("/{date}/schedule", response_model=DayContextSchema)
async def schedule_day(
    date: datetime.date,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
    template_id: UUID | None = None,
) -> DayContextSchema:
    """Schedule a specific day with tasks from routines."""
    context = await handler.schedule_day(
        user_id=user.id, date=date, template_id=template_id
    )
    return map_day_context_to_schema(context)


class UpdateDayRequest(BaseModel):
    """Request body for updating a day."""

    status: value_objects.DayStatus | None = None
    template_id: UUID | None = None


@router.patch("/{date}", response_model=DaySchema)
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[UpdateDayHandler, Depends(get_update_day_handler)],
) -> DaySchema:
    """Update a day's status or template."""
    day = await handler.update_day(
        user_id=user.id,
        date=date,
        status=request.status,
        template_id=request.template_id,
    )
    return map_day_to_schema(day)


# ============================================================================
# Templates
# ============================================================================


@router.get("/templates", response_model=list[DayTemplateSchema])
async def get_templates(
    user: Annotated[UserEntity, Depends(get_current_user)],
    list_day_templates_handler: Annotated[
        ListDayTemplatesHandler, Depends(get_list_day_templates_handler)
    ],
) -> list[DayTemplateSchema]:
    """Get all available day templates."""
    result = await list_day_templates_handler.run(
        user_id=user.id,
    )
    templates = result if isinstance(result, list) else result.items
    return [map_day_template_to_schema(template) for template in templates]
