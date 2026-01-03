"""Router for TaskDefinition CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands.task_definition import (
    BulkCreateTaskDefinitionsHandler,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionHandler,
)
from planned.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    ListTaskDefinitionsHandler,
)
from planned.domain import value_objects
from planned.domain.entities import TaskDefinitionEntity, UserEntity
from planned.infrastructure.data.default_task_definitions import (
    DEFAULT_TASK_DEFINITIONS,
)
from planned.presentation.api.schemas import TaskDefinitionSchema
from planned.presentation.api.schemas.mappers import map_task_definition_to_schema

from .dependencies.services import (
    get_bulk_create_task_definitions_handler,
    get_create_task_definition_handler,
    get_delete_task_definition_handler,
    get_get_task_definition_handler,
    get_list_task_definitions_handler,
    get_update_task_definition_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/available")
async def get_available_task_definitions() -> list[dict]:
    """Get the curated list of available task definitions that users can import.

    Returns:
        List of task definition dictionaries (without user_id)
    """
    return DEFAULT_TASK_DEFINITIONS


@router.get("/{uuid}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    get_task_definition_handler: Annotated[
        GetTaskDefinitionHandler, Depends(get_get_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    task_definition = await get_task_definition_handler.run(
        user_id=user.id, task_definition_id=uuid
    )
    return map_task_definition_to_schema(task_definition)


@router.get("/", response_model=list[TaskDefinitionSchema])
async def list_task_definitions(
    user: Annotated[UserEntity, Depends(get_current_user)],
    list_task_definitions_handler: Annotated[
        ListTaskDefinitionsHandler, Depends(get_list_task_definitions_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskDefinitionSchema]:
    """List task definitions with pagination."""
    result = await list_task_definitions_handler.run(
        user_id=user.id,
        limit=limit,
        offset=offset,
        paginate=False,
    )
    task_definitions: list[TaskDefinitionEntity] = (
        result if isinstance(result, list) else result.items
    )
    return [map_task_definition_to_schema(td) for td in task_definitions]


@router.post("/", response_model=TaskDefinitionSchema)
async def create_task_definition(
    task_definition_data: TaskDefinitionSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_task_definition_handler: Annotated[
        CreateTaskDefinitionHandler, Depends(get_create_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    # Convert schema to entity
    task_definition = TaskDefinitionEntity(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    created = await create_task_definition_handler.run(
        user_id=user.id, task_definition=task_definition
    )
    return map_task_definition_to_schema(created)


@router.post("/bulk", response_model=list[TaskDefinitionSchema])
async def bulk_create_task_definitions(
    task_definitions_data: list[dict],
    user: Annotated[UserEntity, Depends(get_current_user)],
    bulk_create_task_definitions_handler: Annotated[
        BulkCreateTaskDefinitionsHandler,
        Depends(get_bulk_create_task_definitions_handler),
    ],
) -> list[TaskDefinitionSchema]:
    """Bulk create task definitions."""
    # Convert dictionaries to entities
    task_definitions = []
    for data in task_definitions_data:
        if "user_id" not in data:
            data["user_id"] = user.id
        task_definition = TaskDefinitionEntity(**data)
        task_definitions.append(task_definition)

    created = await bulk_create_task_definitions_handler.run(
        user_id=user.id, task_definitions=tuple(task_definitions)
    )
    return [map_task_definition_to_schema(td) for td in created]


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    task_definition_data: TaskDefinitionSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    update_task_definition_handler: Annotated[
        UpdateTaskDefinitionHandler, Depends(get_update_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Update a task definition."""
    # Convert schema to entity
    task_definition = TaskDefinitionEntity(
        id=uuid,
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    updated = await update_task_definition_handler.run(
        user_id=user.id,
        task_definition_id=uuid,
        task_definition_data=task_definition,
    )
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    delete_task_definition_handler: Annotated[
        DeleteTaskDefinitionHandler, Depends(get_delete_task_definition_handler)
    ],
) -> None:
    """Delete a task definition."""
    await delete_task_definition_handler.run(user_id=user.id, task_definition_id=uuid)
