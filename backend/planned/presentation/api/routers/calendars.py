"""Router for Calendar CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands import (
    CreateEntityHandler,
    DeleteEntityHandler,
    UpdateEntityHandler,
)
from planned.application.queries import GetEntityHandler, ListEntitiesHandler
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, UserEntity
from planned.presentation.api.schemas import CalendarSchema
from planned.presentation.api.schemas.mappers import map_calendar_to_schema

from .dependencies.services import (
    get_create_entity_handler,
    get_delete_entity_handler,
    get_get_entity_handler,
    get_list_entities_handler,
    get_update_entity_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarSchema)
async def get_calendar(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetEntityHandler, Depends(get_get_entity_handler)],
) -> CalendarSchema:
    """Get a single calendar by ID."""
    calendar: CalendarEntity = await handler.get_entity(
        user_id=user.id,
        repository_name="calendars",
        entity_id=uuid,
    )
    return map_calendar_to_schema(calendar)


@router.get("/", response_model=value_objects.PagedQueryResponse[CalendarSchema])
async def list_calendars(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ListEntitiesHandler, Depends(get_list_entities_handler)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[CalendarSchema]:
    """List calendars with pagination."""
    result: (
        list[CalendarEntity] | value_objects.PagedQueryResponse[CalendarEntity]
    ) = await handler.list_entities(
        user_id=user.id,
        repository_name="calendars",
        limit=limit,
        offset=offset,
        paginate=True,
    )
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
    handler: Annotated[CreateEntityHandler, Depends(get_create_entity_handler)],
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
    created = await handler.create_entity(
        user_id=user.id,
        repository_name="calendars",
        entity=calendar,
    )
    return map_calendar_to_schema(created)


@router.put("/{uuid}", response_model=CalendarSchema)
async def update_calendar(
    uuid: UUID,
    calendar_data: CalendarSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[UpdateEntityHandler, Depends(get_update_entity_handler)],
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
    updated = await handler.update_entity(
        user_id=user.id,
        repository_name="calendars",
        entity_id=uuid,
        entity_data=calendar,
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_calendar(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[DeleteEntityHandler, Depends(get_delete_entity_handler)],
) -> None:
    """Delete a calendar."""
    await handler.delete_entity(
        user_id=user.id,
        repository_name="calendars",
        entity_id=uuid,
    )
