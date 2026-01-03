"""Router for TaskDefinition CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands import (
    BulkCreateEntitiesCommand,
    CreateEntityCommand,
    DeleteEntityCommand,
    UpdateEntityCommand,
)
from planned.application.mediator import Mediator
from planned.application.queries import GetEntityQuery, ListEntitiesQuery
from planned.domain.entities import TaskDefinitionEntity, TaskEntity, UserEntity
from planned.infrastructure.data.default_task_definitions import (
    DEFAULT_TASK_DEFINITIONS,
)
from planned.presentation.api.schemas import TaskDefinitionSchema
from planned.presentation.api.schemas.mappers import map_task_definition_to_schema

from .dependencies.services import get_mediator
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
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    query = GetEntityQuery[TaskDefinitionEntity](
        user_id=user.id,
        entity_id=uuid,
        repository_name="task_definitions",
    )
    task_definition = await mediator.query(query)
    return map_task_definition_to_schema(task_definition)


@router.get("/", response_model=list[TaskDefinitionSchema])
async def list_task_definitions(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskDefinitionSchema]:
    """List task definitions with pagination."""
    query = ListEntitiesQuery[TaskDefinitionEntity](
        user_id=user.id,
        repository_name="task_definitions",
        limit=limit,
        offset=offset,
        paginate=False,
    )
    result = await mediator.query(query)
    task_definitions = cast("list[TaskDefinitionEntity]", result)
    return [map_task_definition_to_schema(td) for td in task_definitions]


@router.post("/", response_model=TaskDefinitionSchema)
async def create_task_definition(
    task_definition_data: TaskDefinitionSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    # Convert schema to entity
    task_definition = TaskDefinitionEntity(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    command = CreateEntityCommand[TaskDefinitionEntity](
        user_id=user.id,
        repository_name="task_definitions",
        entity=task_definition,
    )
    created = await mediator.execute(command)
    return map_task_definition_to_schema(created)


@router.post("/bulk", response_model=list[TaskDefinitionSchema])
async def bulk_create_task_definitions(
    task_definitions_data: list[dict],
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> list[TaskDefinitionSchema]:
    """Bulk create task definitions."""
    # Convert dictionaries to entities
    task_definitions = []
    for data in task_definitions_data:
        if "user_id" not in data:
            data["user_id"] = user.id
        task_definition = TaskDefinitionEntity(**data)
        task_definitions.append(task_definition)

    command = BulkCreateEntitiesCommand[TaskDefinitionEntity](
        user_id=user.id,
        repository_name="task_definitions",
        entities=tuple(task_definitions),
    )
    created = await mediator.execute(command)
    return [map_task_definition_to_schema(td) for td in created]


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    task_definition_data: TaskDefinitionSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
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
    command = UpdateEntityCommand[TaskDefinitionEntity](
        user_id=user.id,
        repository_name="task_definitions",
        entity_id=uuid,
        entity_data=task_definition,
    )
    updated = await mediator.execute(command)
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> None:
    """Delete a task definition."""
    command = DeleteEntityCommand(
        user_id=user.id,
        repository_name="task_definitions",
        entity_id=uuid,
    )
    await mediator.execute(command)
