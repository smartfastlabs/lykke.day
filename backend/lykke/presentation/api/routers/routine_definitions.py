"""Router for RoutineDefinition CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.routine_definition import (
    AddRoutineDefinitionTaskCommand,
    AddRoutineDefinitionTaskHandler,
    CreateRoutineDefinitionCommand,
    CreateRoutineDefinitionHandler,
    DeleteRoutineDefinitionCommand,
    DeleteRoutineDefinitionHandler,
    RemoveRoutineDefinitionTaskCommand,
    RemoveRoutineDefinitionTaskHandler,
    UpdateRoutineDefinitionCommand,
    UpdateRoutineDefinitionHandler,
    UpdateRoutineDefinitionTaskCommand,
    UpdateRoutineDefinitionTaskHandler,
)
from lykke.application.queries.routine_definition import (
    GetRoutineDefinitionHandler,
    GetRoutineDefinitionQuery,
    SearchRoutineDefinitionsHandler,
    SearchRoutineDefinitionsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    RoutineDefinitionCreateSchema,
    RoutineDefinitionSchema,
    RoutineDefinitionTaskCreateSchema,
    RoutineDefinitionTaskUpdateSchema,
    RoutineDefinitionUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_routine_definition_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .routine_definition_mappers import (
    create_schema_to_entity,
    task_create_schema_to_vo,
    task_update_schema_to_partial_vo,
    update_schema_to_update_object,
)
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineDefinitionSchema)
async def get_routine_definition(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> RoutineDefinitionSchema:
    """Get a single routine definition by ID."""
    get_routine_definition_handler = query_factory.create(GetRoutineDefinitionHandler)
    routine_definition = await get_routine_definition_handler.handle(
        GetRoutineDefinitionQuery(routine_definition_id=uuid)
    )
    return map_routine_definition_to_schema(routine_definition)


@router.post("/", response_model=PagedResponseSchema[RoutineDefinitionSchema])
async def search_routine_definitions(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.RoutineDefinitionQuery],
) -> PagedResponseSchema[RoutineDefinitionSchema]:
    """Search routine definitions with pagination and optional filters."""
    list_routine_definitions_handler = query_factory.create(
        SearchRoutineDefinitionsHandler
    )
    search_query = build_search_query(query, value_objects.RoutineDefinitionQuery)
    result = await list_routine_definitions_handler.handle(
        SearchRoutineDefinitionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_routine_definition_to_schema)


@router.post(
    "/create",
    response_model=RoutineDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_routine_definition(
    routine_definition_data: RoutineDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Create a new routine definition."""
    create_routine_definition_handler = command_factory.create(
        CreateRoutineDefinitionHandler
    )
    routine_definition = create_schema_to_entity(routine_definition_data, user.id)
    created = await create_routine_definition_handler.handle(
        CreateRoutineDefinitionCommand(routine_definition=routine_definition)
    )
    return map_routine_definition_to_schema(created)


@router.put("/{uuid}", response_model=RoutineDefinitionSchema)
async def update_routine_definition(
    uuid: UUID,
    update_data: RoutineDefinitionUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Update an existing routine definition."""
    update_routine_definition_handler = command_factory.create(
        UpdateRoutineDefinitionHandler
    )
    update_object = update_schema_to_update_object(update_data)
    updated = await update_routine_definition_handler.handle(
        UpdateRoutineDefinitionCommand(
            routine_definition_id=uuid,
            update_data=update_object,
        )
    )
    return map_routine_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine_definition(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a routine definition."""
    delete_routine_definition_handler = command_factory.create(
        DeleteRoutineDefinitionHandler
    )
    await delete_routine_definition_handler.handle(
        DeleteRoutineDefinitionCommand(routine_definition_id=uuid)
    )


@router.post(
    "/{uuid}/tasks",
    response_model=RoutineDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_routine_definition_task(
    uuid: UUID,
    routine_task: RoutineDefinitionTaskCreateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Attach a task definition to a routine definition."""
    add_routine_definition_task_handler = command_factory.create(
        AddRoutineDefinitionTaskHandler
    )
    updated = await add_routine_definition_task_handler.handle(
        AddRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task=task_create_schema_to_vo(routine_task),
        )
    )
    return map_routine_definition_to_schema(updated)


@router.put(
    "/{uuid}/tasks/{routine_definition_task_id}",
    response_model=RoutineDefinitionSchema,
)
async def update_routine_definition_task(
    uuid: UUID,
    routine_definition_task_id: UUID,
    routine_task_update: RoutineDefinitionTaskUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Update an attached routine definition task (name/schedule)."""
    update_routine_definition_task_handler = command_factory.create(
        UpdateRoutineDefinitionTaskHandler
    )
    updated = await update_routine_definition_task_handler.handle(
        UpdateRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task_id=routine_definition_task_id,
            routine_definition_task=task_update_schema_to_partial_vo(
                routine_task_update, routine_definition_task_id
            ),
        )
    )
    return map_routine_definition_to_schema(updated)


@router.delete(
    "/{uuid}/tasks/{routine_definition_task_id}",
    response_model=RoutineDefinitionSchema,
)
async def remove_routine_definition_task(
    uuid: UUID,
    routine_definition_task_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Detach a routine definition task from a routine definition by RoutineDefinitionTask.id."""
    remove_routine_definition_task_handler = command_factory.create(
        RemoveRoutineDefinitionTaskHandler
    )
    updated = await remove_routine_definition_task_handler.handle(
        RemoveRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task_id=routine_definition_task_id,
        )
    )
    return map_routine_definition_to_schema(updated)
