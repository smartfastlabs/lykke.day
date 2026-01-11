"""Router for TaskDefinition CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from lykke.application.commands.task_definition import (
    BulkCreateTaskDefinitionsHandler,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionHandler,
)
from lykke.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    SearchTaskDefinitionsHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain import data_objects
from lykke.infrastructure.data.default_task_definitions import (
    DEFAULT_TASK_DEFINITIONS,
)
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TaskDefinitionCreateSchema,
    TaskDefinitionSchema,
    TaskDefinitionUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_task_definition_to_schema

from .dependencies.commands.task_definition import (
    get_bulk_create_task_definitions_handler,
    get_create_task_definition_handler,
    get_delete_task_definition_handler,
    get_update_task_definition_handler,
)
from .dependencies.queries.task_definition import (
    get_get_task_definition_handler,
    get_list_task_definitions_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/available/")
async def get_available_task_definitions() -> list[dict]:
    """Get the curated list of available task definitions that users can import.

    Returns:
        List of task definition dictionaries (without user_id)
    """
    return DEFAULT_TASK_DEFINITIONS


@router.get("/{uuid}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    uuid: UUID,
    get_task_definition_handler: Annotated[
        GetTaskDefinitionHandler, Depends(get_get_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Get a single task definition by ID."""
    task_definition = await get_task_definition_handler.run(task_definition_id=uuid)
    return map_task_definition_to_schema(task_definition)


@router.post("/", response_model=PagedResponseSchema[TaskDefinitionSchema])
async def search_task_definitions(
    list_task_definitions_handler: Annotated[
        SearchTaskDefinitionsHandler, Depends(get_list_task_definitions_handler)
    ],
    query: QuerySchema[value_objects.TaskDefinitionQuery],
) -> PagedResponseSchema[TaskDefinitionSchema]:
    """Search task definitions with pagination and optional filters."""
    # Build the search query from the request
    filters = query.filters or value_objects.TaskDefinitionQuery()
    search_query = value_objects.TaskDefinitionQuery(
        limit=query.limit,
        offset=query.offset,
        created_before=filters.created_before,
        created_after=filters.created_after,
        order_by=filters.order_by,
        order_by_desc=filters.order_by_desc,
    )
    result = await list_task_definitions_handler.run(search_query=search_query)
    task_definition_schemas = [map_task_definition_to_schema(td) for td in result.items]
    return PagedResponseSchema(
        items=task_definition_schemas,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.post("/create", response_model=TaskDefinitionSchema)
async def create_task_definition(
    task_definition_data: TaskDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_task_definition_handler: Annotated[
        CreateTaskDefinitionHandler, Depends(get_create_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Create a new task definition."""
    # Convert schema to data object
    task_definition = data_objects.TaskDefinition(
        user_id=user.id,
        name=task_definition_data.name,
        description=task_definition_data.description,
        type=task_definition_data.type,
    )
    created = await create_task_definition_handler.run(task_definition=task_definition)
    return map_task_definition_to_schema(created)


@router.post("/bulk/", response_model=list[TaskDefinitionSchema])
async def bulk_create_task_definitions(
    task_definitions_data: list[dict],
    user: Annotated[UserEntity, Depends(get_current_user)],
    bulk_create_task_definitions_handler: Annotated[
        BulkCreateTaskDefinitionsHandler,
        Depends(get_bulk_create_task_definitions_handler),
    ],
) -> list[TaskDefinitionSchema]:
    """Bulk create task definitions."""
    # Convert dictionaries to data objects
    task_definitions = []
    for data in task_definitions_data:
        if "user_id" not in data:
            data["user_id"] = user.id
        task_definition = data_objects.TaskDefinition(**data)
        task_definitions.append(task_definition)

    created = await bulk_create_task_definitions_handler.run(
        task_definitions=tuple(task_definitions)
    )
    return [map_task_definition_to_schema(td) for td in created]


@router.put("/{uuid}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    uuid: UUID,
    update_data: TaskDefinitionUpdateSchema,
    update_task_definition_handler: Annotated[
        UpdateTaskDefinitionHandler, Depends(get_update_task_definition_handler)
    ],
) -> TaskDefinitionSchema:
    """Update a task definition."""
    # Convert schema to update object
    from lykke.domain.value_objects import TaskDefinitionUpdateObject

    update_object = TaskDefinitionUpdateObject(
        name=update_data.name,
        description=update_data.description,
        type=update_data.type,
    )
    updated = await update_task_definition_handler.run(
        task_definition_id=uuid,
        update_data=update_object,
    )
    return map_task_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_task_definition(
    uuid: UUID,
    delete_task_definition_handler: Annotated[
        DeleteTaskDefinitionHandler, Depends(get_delete_task_definition_handler)
    ],
) -> None:
    """Delete a task definition."""
    await delete_task_definition_handler.run(task_definition_id=uuid)
