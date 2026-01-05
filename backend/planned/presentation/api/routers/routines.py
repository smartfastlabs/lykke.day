"""Router for Routine CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.queries.routine import GetRoutineHandler, SearchRoutinesHandler
from planned.domain import value_objects
from planned.domain.entities import RoutineEntity, UserEntity
from planned.presentation.api.schemas import RoutineSchema
from planned.presentation.api.schemas.mappers import map_routine_to_schema

from .dependencies.queries.routine import (
    get_get_routine_handler,
    get_list_routines_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineSchema)
async def get_routine(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    get_routine_handler: Annotated[GetRoutineHandler, Depends(get_get_routine_handler)],
) -> RoutineSchema:
    """Get a single routine by ID."""
    routine = await get_routine_handler.run(routine_id=uuid)
    return map_routine_to_schema(routine)


@router.get("/", response_model=value_objects.PagedQueryResponse[RoutineSchema])
async def list_routines(
    user: Annotated[UserEntity, Depends(get_current_user)],
    list_routines_handler: Annotated[
        SearchRoutinesHandler, Depends(get_list_routines_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[RoutineSchema]:
    """List routines with pagination."""
    result = await list_routines_handler.run(
        search_query=value_objects.RoutineQuery(limit=limit, offset=offset),
    )
    paged_response = result
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
