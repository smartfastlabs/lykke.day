"""Router for Routine CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.queries import GetEntityHandler, ListEntitiesHandler
from planned.domain import value_objects
from planned.domain.entities import RoutineEntity, UserEntity
from planned.presentation.api.schemas import RoutineSchema
from planned.presentation.api.schemas.mappers import map_routine_to_schema

from .dependencies.services import get_get_entity_handler, get_list_entities_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineSchema)
async def get_routine(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetEntityHandler, Depends(get_get_entity_handler)],
) -> RoutineSchema:
    """Get a single routine by ID."""
    routine: RoutineEntity = await handler.get_entity(
        user_id=user.id,
        repository_name="routines",
        entity_id=uuid,
    )
    return map_routine_to_schema(routine)


@router.get("/", response_model=value_objects.PagedQueryResponse[RoutineSchema])
async def list_routines(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ListEntitiesHandler, Depends(get_list_entities_handler)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[RoutineSchema]:
    """List routines with pagination."""
    result: (
        list[RoutineEntity] | value_objects.PagedQueryResponse[RoutineEntity]
    ) = await handler.list_entities(
        user_id=user.id,
        repository_name="routines",
        limit=limit,
        offset=offset,
        paginate=True,
    )
    paged_response = cast("value_objects.PagedQueryResponse[RoutineEntity]", result)
    # Convert entities to schemas
    routine_schemas = [map_routine_to_schema(r) for r in paged_response.items]
    return value_objects.PagedQueryResponse(
        items=routine_schemas,
        total=paged_response.total,
        limit=paged_response.limit,
        offset=paged_response.offset,
        has_next=paged_response.has_next,
        has_previous=paged_response.has_previous,
    )
