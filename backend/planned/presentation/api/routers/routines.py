"""Router for Routine CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.mediator import Mediator
from planned.application.queries import GetEntityQuery, ListEntitiesQuery
from planned.domain import value_objects
from planned.domain.entities import RoutineEntity, UserEntity
from planned.presentation.api.schemas import RoutineSchema
from planned.presentation.api.schemas.mappers import map_routine_to_schema

from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineSchema)
async def get_routine(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> RoutineSchema:
    """Get a single routine by ID."""
    query = GetEntityQuery[RoutineEntity](
        user_id=user.id,
        entity_id=uuid,
        repository_name="routines",
    )
    routine = await mediator.query(query)
    return map_routine_to_schema(routine)


@router.get("/", response_model=value_objects.PagedQueryResponse[RoutineSchema])
async def list_routines(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[RoutineSchema]:
    """List routines with pagination."""
    query = ListEntitiesQuery[RoutineEntity](
        user_id=user.id,
        repository_name="routines",
        limit=limit,
        offset=offset,
        paginate=True,
    )
    result = await mediator.query(query)
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
