"""Router for Calendar CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands import (
    CreateEntityCommand,
    DeleteEntityCommand,
    UpdateEntityCommand,
)
from planned.application.mediator import Mediator
from planned.application.queries import GetEntityQuery, ListEntitiesQuery
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, UserEntity
from planned.presentation.api.schemas import CalendarSchema
from planned.presentation.api.schemas.mappers import map_calendar_to_schema

from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarSchema)
async def get_calendar(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> CalendarSchema:
    """Get a single calendar by ID."""
    query = GetEntityQuery[CalendarEntity](
        user_id=user.id,
        entity_id=uuid,
        repository_name="calendars",
    )
    calendar = await mediator.query(query)
    return map_calendar_to_schema(calendar)


@router.get("/", response_model=value_objects.PagedQueryResponse[CalendarSchema])
async def list_calendars(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[CalendarSchema]:
    """List calendars with pagination."""
    query = ListEntitiesQuery[CalendarEntity](
        user_id=user.id,
        repository_name="calendars",
        limit=limit,
        offset=offset,
        paginate=True,
    )
    result = await mediator.query(query)
    paged_response = cast("value_objects.PagedQueryResponse[CalendarEntity]", result)
    # Convert entities to schemas
    calendar_schemas = [map_calendar_to_schema(c) for c in paged_response.items]
    return value_objects.PagedQueryResponse(
        items=calendar_schemas,
        total=paged_response.total,
        limit=paged_response.limit,
        offset=paged_response.offset,
        has_next=paged_response.has_next,
        has_previous=paged_response.has_previous,
    )


@router.post("/", response_model=CalendarSchema)
async def create_calendar(
    calendar_data: CalendarSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> CalendarSchema:
    """Create a new calendar."""
    # Convert schema to entity (id is optional for create, entity will generate it if None)
    calendar = CalendarEntity(
        id=calendar_data.id if calendar_data.id else None,  # type: ignore[arg-type]
        user_id=user.id,
        name=calendar_data.name,
        auth_token_id=calendar_data.auth_token_id,
        platform_id=calendar_data.platform_id,
        platform=calendar_data.platform,
        last_sync_at=calendar_data.last_sync_at,
    )
    command = CreateEntityCommand[CalendarEntity](
        user_id=user.id,
        repository_name="calendars",
        entity=calendar,
    )
    created = await mediator.execute(command)
    return map_calendar_to_schema(created)


@router.put("/{uuid}", response_model=CalendarSchema)
async def update_calendar(
    uuid: UUID,
    calendar_data: CalendarSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> CalendarSchema:
    """Update a calendar."""
    # Convert schema to entity
    calendar = CalendarEntity(
        id=uuid,
        user_id=user.id,
        name=calendar_data.name,
        auth_token_id=calendar_data.auth_token_id,
        platform_id=calendar_data.platform_id,
        platform=calendar_data.platform,
        last_sync_at=calendar_data.last_sync_at,
    )
    command = UpdateEntityCommand[CalendarEntity](
        user_id=user.id,
        repository_name="calendars",
        entity_id=uuid,
        entity_data=calendar,
    )
    updated = await mediator.execute(command)
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_calendar(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> None:
    """Delete a calendar."""
    command = DeleteEntityCommand(
        user_id=user.id,
        repository_name="calendars",
        entity_id=uuid,
    )
    await mediator.execute(command)
