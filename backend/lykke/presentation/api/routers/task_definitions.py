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
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    get_task_definition_handler = query_factory.create(GetTaskDefinitionHandler)
    task_definition = await get_task_definition_handler.handle(
        GetTaskDefinitionQuery(task_definition_id=uuid)
    )
    return map_task_definition_to_schema(task_definition)


@router.post("/", response_model=PagedResponseSchema[TaskDefinitionSchema])
async def search_task_definitions(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.TaskDefinitionQuery],
) -> PagedResponseSchema[TaskDefinitionSchema]:
    """Search task definitions with pagination and optional filters."""
    list_task_definitions_handler = query_factory.create(SearchTaskDefinitionsHandler)
    search_query = build_search_query(query, value_objects.TaskDefinitionQuery)
    result = await list_task_definitions_handler.handle(
        SearchTaskDefinitionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_task_definition_to_schema)


@router.post("/create", response_model=TaskDefinitionSchema)
async def create_task_definition(
    task_definition_data: TaskDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    create_task_definition_handler = command_factory.create(CreateTaskDefinitionHandler)
    # Convert schema to data object
    task_definition = TaskDefinitionEntity(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    created = await create_task_definition_handler.handle(
        CreateTaskDefinitionCommand(task_definition=task_definition)
    )
    return map_task_definition_to_schema(created)


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    update_data: TaskDefinitionUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> TaskDefinitionSchema:
    """Update a task definition."""
    update_task_definition_handler = command_factory.create(UpdateTaskDefinitionHandler)
    # Convert schema to update object
    from lykke.domain.value_objects import TaskDefinitionUpdateObject

    update_object = TaskDefinitionUpdateObject(
        name=update_data.name,
        description=update_data.description,
        type=update_data.type,
    )
    updated = await update_task_definition_handler.handle(
        UpdateTaskDefinitionCommand(task_definition_id=uuid, update_data=update_object)
    )
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a task definition."""
    delete_task_definition_handler = command_factory.create(DeleteTaskDefinitionHandler)
    await delete_task_definition_handler.handle(
        DeleteTaskDefinitionCommand(task_definition_id=uuid)
    )
