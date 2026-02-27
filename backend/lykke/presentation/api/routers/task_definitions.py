"""Router for TaskDefinition CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.task_definition import (
    CreateTaskDefinitionCommand,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionCommand,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionCommand,
    UpdateTaskDefinitionHandler,
)
from lykke.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    GetTaskDefinitionQuery,
    SearchTaskDefinitionsHandler,
    SearchTaskDefinitionsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import TaskDefinitionEntity, UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TaskDefinitionCreateSchema,
    TaskDefinitionSchema,
    TaskDefinitionUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_task_definition_to_schema

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    uuid: UUID,
    handler: Annotated[
        GetTaskDefinitionHandler, Depends(create_query_handler(GetTaskDefinitionHandler))
    ],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    task_definition = await handler.handle(
        GetTaskDefinitionQuery(task_definition_id=uuid)
    )
    return map_task_definition_to_schema(task_definition)


@router.post("/", response_model=PagedResponseSchema[TaskDefinitionSchema])
async def search_task_definitions(
    query: QuerySchema[value_objects.TaskDefinitionQuery],
    handler: Annotated[
        SearchTaskDefinitionsHandler,
        Depends(create_query_handler(SearchTaskDefinitionsHandler)),
    ],
) -> PagedResponseSchema[TaskDefinitionSchema]:
    """Search task definitions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.TaskDefinitionQuery)
    result = await handler.handle(
        SearchTaskDefinitionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_task_definition_to_schema)


@router.post("/create", response_model=TaskDefinitionSchema)
async def create_task_definition(
    task_definition_data: TaskDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        CreateTaskDefinitionHandler,
        Depends(create_command_handler(CreateTaskDefinitionHandler)),
    ],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    # Convert schema to data object
    task_definition = TaskDefinitionEntity(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    created = await handler.handle(
        CreateTaskDefinitionCommand(task_definition=task_definition)
    )
    return map_task_definition_to_schema(created)


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    update_data: TaskDefinitionUpdateSchema,
    handler: Annotated[
        UpdateTaskDefinitionHandler,
        Depends(create_command_handler(UpdateTaskDefinitionHandler)),
    ],
) -> TaskDefinitionSchema:
    """Update a task definition."""
    from lykke.domain.value_objects import TaskDefinitionUpdateObject

    update_object = TaskDefinitionUpdateObject(
        name=update_data.name,
        description=update_data.description,
        type=update_data.type,
    )
    updated = await handler.handle(
        UpdateTaskDefinitionCommand(task_definition_id=uuid, update_data=update_object)
    )
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    handler: Annotated[
        DeleteTaskDefinitionHandler,
        Depends(create_command_handler(DeleteTaskDefinitionHandler)),
    ],
) -> None:
    """Delete a task definition."""
    await handler.handle(DeleteTaskDefinitionCommand(task_definition_id=uuid))
