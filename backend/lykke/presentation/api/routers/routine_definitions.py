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

from .dependencies.factories import create_command_handler, create_query_handler
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
    handler: Annotated[GetRoutineDefinitionHandler, Depends(create_query_handler(GetRoutineDefinitionHandler))],
) -> RoutineDefinitionSchema:
    """Get a single routine definition by ID."""
    routine_definition = await handler.handle(
        GetRoutineDefinitionQuery(routine_definition_id=uuid)
    )
    return map_routine_definition_to_schema(routine_definition)


@router.post("/", response_model=PagedResponseSchema[RoutineDefinitionSchema])
async def search_routine_definitions(
    handler: Annotated[SearchRoutineDefinitionsHandler, Depends(create_query_handler(SearchRoutineDefinitionsHandler))],
    query: QuerySchema[value_objects.RoutineDefinitionQuery],
) -> PagedResponseSchema[RoutineDefinitionSchema]:
    """Search routine definitions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.RoutineDefinitionQuery)
    result = await handler.handle(
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
    handler: Annotated[CreateRoutineDefinitionHandler, Depends(create_command_handler(CreateRoutineDefinitionHandler))],
) -> RoutineDefinitionSchema:
    """Create a new routine definition."""
    routine_definition = create_schema_to_entity(routine_definition_data, user.id)
    created = await handler.handle(
        CreateRoutineDefinitionCommand(routine_definition=routine_definition)
    )
    return map_routine_definition_to_schema(created)


@router.put("/{uuid}", response_model=RoutineDefinitionSchema)
async def update_routine_definition(
    uuid: UUID,
    update_data: RoutineDefinitionUpdateSchema,
    handler: Annotated[UpdateRoutineDefinitionHandler, Depends(create_command_handler(UpdateRoutineDefinitionHandler))],
) -> RoutineDefinitionSchema:
    """Update an existing routine definition."""
    update_object = update_schema_to_update_object(update_data)
    updated = await handler.handle(
        UpdateRoutineDefinitionCommand(
            routine_definition_id=uuid,
            update_data=update_object,
        )
    )
    return map_routine_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine_definition(
    uuid: UUID,
    handler: Annotated[DeleteRoutineDefinitionHandler, Depends(create_command_handler(DeleteRoutineDefinitionHandler))],
) -> None:
    """Delete a routine definition."""
    await handler.handle(
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
    handler: Annotated[AddRoutineDefinitionTaskHandler, Depends(create_command_handler(AddRoutineDefinitionTaskHandler))],
) -> RoutineDefinitionSchema:
    """Attach a task definition to a routine definition."""
    updated = await handler.handle(
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
    handler: Annotated[UpdateRoutineDefinitionTaskHandler, Depends(create_command_handler(UpdateRoutineDefinitionTaskHandler))],
) -> RoutineDefinitionSchema:
    """Update an attached routine definition task (name/schedule)."""
    updated = await handler.handle(
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
    handler: Annotated[RemoveRoutineDefinitionTaskHandler, Depends(create_command_handler(RemoveRoutineDefinitionTaskHandler))],
) -> RoutineDefinitionSchema:
    """Detach a routine definition task from a routine definition by RoutineDefinitionTask.id."""
    updated = await handler.handle(
        RemoveRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task_id=routine_definition_task_id,
        )
    )
    return map_routine_definition_to_schema(updated)
