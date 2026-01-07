"""Routes for planning operations."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from lykke.application.commands import ScheduleDayHandler
from lykke.application.queries import PreviewDayHandler
from lykke.application.queries.routine import SearchRoutinesHandler
from lykke.core.utils.dates import get_current_date, get_tomorrows_date
from lykke.domain import value_objects
from lykke.presentation.api.schemas import DayContextSchema, RoutineSchema
from lykke.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_routine_to_schema,
)

from .dependencies.queries.routine import get_list_routines_handler
from .dependencies.services import get_preview_day_handler, get_schedule_day_handler

router = APIRouter()


@router.get("/routines/", response_model=list[RoutineSchema])
async def list_routines(
    list_routines_handler: Annotated[
        SearchRoutinesHandler, Depends(get_list_routines_handler)
    ],
) -> list[RoutineSchema]:
    """Get all routines for the current user."""
    result = await list_routines_handler.run()
    return [map_routine_to_schema(routine) for routine in result.items]


# ============================================================================
# Preview Queries
# ============================================================================


@router.get("/preview/today", response_model=DayContextSchema)
async def preview_today(
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what today would look like if scheduled."""
    context = await handler.preview_day(date=get_current_date())
    return map_day_context_to_schema(context)


@router.get("/tomorrow/preview", response_model=DayContextSchema)
async def preview_tomorrow(
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what tomorrow would look like if scheduled."""
    context = await handler.preview_day(date=get_tomorrows_date())
    return map_day_context_to_schema(context)


@router.get("/date/{date}/preview", response_model=DayContextSchema)
async def preview_date(
    date: datetime.date,
    handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
) -> DayContextSchema:
    """Preview what a specific date would look like if scheduled."""
    context = await handler.preview_day(date=date)
    return map_day_context_to_schema(context)


# ============================================================================
# Schedule Commands
# ============================================================================


@router.put("/schedule/today", response_model=DayContextSchema)
async def schedule_today(
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule today with tasks from routines."""
    context = await handler.schedule_day(date=get_current_date())
    return map_day_context_to_schema(context)


@router.put("/tomorrow/schedule", response_model=DayContextSchema)
async def schedule_tomorrow(
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule tomorrow with tasks from routines."""
    context = await handler.schedule_day(date=get_tomorrows_date())
    return map_day_context_to_schema(context)


@router.put("/date/{date}/schedule", response_model=DayContextSchema)
async def schedule_date(
    date: datetime.date,
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule a specific date with tasks from routines."""
    context = await handler.schedule_day(date=date)
    return map_day_context_to_schema(context)
