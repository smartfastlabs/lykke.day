"""Router for Routine CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from planned.application.commands.routine import (
    AddRoutineTaskHandler,
    CreateRoutineHandler,
    DeleteRoutineHandler,
    RemoveRoutineTaskHandler,
    UpdateRoutineHandler,
    UpdateRoutineTaskHandler,
)
from planned.application.queries.routine import GetRoutineHandler, SearchRoutinesHandler
from planned.domain import value_objects
from planned.domain.entities import RoutineEntity, UserEntity
from planned.domain.value_objects import RoutineUpdateObject
from planned.domain.value_objects.routine import RoutineTask
from planned.presentation.api.schemas import (
    RoutineCreateSchema,
    RoutineSchema,
    RoutineTaskCreateSchema,
    RoutineTaskUpdateSchema,
    RoutineUpdateSchema,
)
from planned.presentation.api.schemas.mappers import map_routine_to_schema

from .dependencies.commands.routine import (
    get_add_routine_task_handler,
    get_create_routine_handler,
    get_delete_routine_handler,
    get_remove_routine_task_handler,
    get_update_routine_handler,
    get_update_routine_task_handler,
)
from .dependencies.queries.routine import (
    get_get_routine_handler,
    get_list_routines_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineSchema)
async def get_routine(
    uuid: UUID,
    get_routine_handler: Annotated[GetRoutineHandler, Depends(get_get_routine_handler)],
) -> RoutineSchema:
    """Get a single routine by ID."""
    routine = await get_routine_handler.run(routine_id=uuid)
    return map_routine_to_schema(routine)


@router.get("/", response_model=value_objects.PagedQueryResponse[RoutineSchema])
async def list_routines(
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


@router.post(
    "/",
    response_model=RoutineSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_routine(
    routine_data: RoutineCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_routine_handler: Annotated[
        CreateRoutineHandler, Depends(get_create_routine_handler)
    ],
) -> RoutineSchema:
    """Create a new routine."""
    routine = RoutineEntity(
        user_id=user.id,
        name=routine_data.name,
        category=routine_data.category,
        routine_schedule=routine_data.routine_schedule,
        description=routine_data.description,
        tasks=routine_data.tasks or [],
    )
    created = await create_routine_handler.run(routine=routine)
    return map_routine_to_schema(created)


@router.put("/{uuid}", response_model=RoutineSchema)
async def update_routine(
    uuid: UUID,
    update_data: RoutineUpdateSchema,
    update_routine_handler: Annotated[
        UpdateRoutineHandler, Depends(get_update_routine_handler)
    ],
) -> RoutineSchema:
    """Update an existing routine."""
    update_object = RoutineUpdateObject(
        name=update_data.name,
        category=update_data.category,
        routine_schedule=update_data.routine_schedule,
        description=update_data.description,
        tasks=update_data.tasks,
    )
    updated = await update_routine_handler.run(
        routine_id=uuid,
        update_data=update_object,
    )
    return map_routine_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(
    uuid: UUID,
    delete_routine_handler: Annotated[
        DeleteRoutineHandler, Depends(get_delete_routine_handler)
    ],
) -> None:
    """Delete a routine."""
    await delete_routine_handler.run(routine_id=uuid)


@router.post(
    "/{uuid}/tasks",
    response_model=RoutineSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_routine_task(
    uuid: UUID,
    routine_task: RoutineTaskCreateSchema,
    add_routine_task_handler: Annotated[
        AddRoutineTaskHandler, Depends(get_add_routine_task_handler)
    ],
) -> RoutineSchema:
    """Attach a task definition to a routine."""
    updated = await add_routine_task_handler.run(
        routine_id=uuid,
        task=RoutineTask(**routine_task.model_dump()),
    )
    return map_routine_to_schema(updated)


@router.put(
    "/{uuid}/tasks/{routine_task_id}",
    response_model=RoutineSchema,
)
async def update_routine_task(
    uuid: UUID,
    routine_task_id: UUID,
    routine_task_update: RoutineTaskUpdateSchema,
    update_routine_task_handler: Annotated[
        UpdateRoutineTaskHandler, Depends(get_update_routine_task_handler)
    ],
) -> RoutineSchema:
    """Update an attached routine task (name/schedule)."""
    updated = await update_routine_task_handler.run(
        routine_id=uuid,
        task_update=RoutineTask(
            id=routine_task_id,
            task_definition_id=UUID(
                "00000000-0000-0000-0000-000000000000"
            ),  # Will be preserved from existing task
            name=routine_task_update.name,
            schedule=routine_task_update.schedule,
        ),
    )
    return map_routine_to_schema(updated)


@router.delete(
    "/{uuid}/tasks/{routine_task_id}",
    response_model=RoutineSchema,
)
async def remove_routine_task(
    uuid: UUID,
    routine_task_id: UUID,
    remove_routine_task_handler: Annotated[
        RemoveRoutineTaskHandler, Depends(get_remove_routine_task_handler)
    ],
) -> RoutineSchema:
    """Detach a routine task from a routine by RoutineTask.id."""
    updated = await remove_routine_task_handler.run(
        routine_id=uuid, routine_task_id=routine_task_id
    )
    return map_routine_to_schema(updated)
