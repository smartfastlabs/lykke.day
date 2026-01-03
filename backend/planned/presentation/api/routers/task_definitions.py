"""Router for TaskDefinition CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands import (
    BulkCreateEntitiesHandler,
    CreateEntityHandler,
    DeleteEntityHandler,
    UpdateEntityHandler,
)
from planned.application.queries import GetEntityHandler, ListEntitiesHandler
from planned.domain import value_objects
from planned.domain.entities import TaskDefinitionEntity, UserEntity
from planned.infrastructure.data.default_task_definitions import (
    DEFAULT_TASK_DEFINITIONS,
)
from planned.presentation.api.schemas import TaskDefinitionSchema
from planned.presentation.api.schemas.mappers import map_task_definition_to_schema

from .dependencies.services import (
    get_bulk_create_entities_handler,
    get_create_entity_handler,
    get_delete_entity_handler,
    get_get_entity_handler,
    get_list_entities_handler,
    get_update_entity_handler,
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
    handler: Annotated[GetEntityHandler, Depends(get_get_entity_handler)],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    task_definition: TaskDefinitionEntity = await handler.get_entity(
        user_id=user.id,
        repository_name="task_definitions",
        entity_id=uuid,
    )
    return map_task_definition_to_schema(task_definition)


@router.get("/", response_model=list[TaskDefinitionSchema])
async def list_task_definitions(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ListEntitiesHandler, Depends(get_list_entities_handler)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskDefinitionSchema]:
    """List task definitions with pagination."""
    result: (
        list[TaskDefinitionEntity]
        | value_objects.PagedQueryResponse[TaskDefinitionEntity]
    ) = await handler.list_entities(
        user_id=user.id,
        repository_name="task_definitions",
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
    handler: Annotated[CreateEntityHandler, Depends(get_create_entity_handler)],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    # Convert schema to entity
    task_definition = TaskDefinitionEntity(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    created = await handler.create_entity(
        user_id=user.id,
        repository_name="task_definitions",
        entity=task_definition,
    )
    return map_task_definition_to_schema(created)


@router.post("/bulk", response_model=list[TaskDefinitionSchema])
async def bulk_create_task_definitions(
    task_definitions_data: list[dict],
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        BulkCreateEntitiesHandler, Depends(get_bulk_create_entities_handler)
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

    created = await handler.bulk_create_entities(
        user_id=user.id,
        repository_name="task_definitions",
        entities=tuple(task_definitions),
    )
    return [map_task_definition_to_schema(td) for td in created]


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    task_definition_data: TaskDefinitionSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[UpdateEntityHandler, Depends(get_update_entity_handler)],
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
    updated = await handler.update_entity(
        user_id=user.id,
        repository_name="task_definitions",
        entity_id=uuid,
        entity_data=task_definition,
    )
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[DeleteEntityHandler, Depends(get_delete_entity_handler)],
) -> None:
    """Delete a task definition."""
    await handler.delete_entity(
        user_id=user.id,
        repository_name="task_definitions",
        entity_id=uuid,
    )
