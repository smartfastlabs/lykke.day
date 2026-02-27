"""Router for TimeBlockDefinition CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.time_block_definition import (
    CreateTimeBlockDefinitionCommand,
    CreateTimeBlockDefinitionHandler,
    DeleteTimeBlockDefinitionCommand,
    DeleteTimeBlockDefinitionHandler,
    UpdateTimeBlockDefinitionCommand,
    UpdateTimeBlockDefinitionHandler,
)
from lykke.application.queries.time_block_definition import (
    GetTimeBlockDefinitionHandler,
    GetTimeBlockDefinitionQuery,
    SearchTimeBlockDefinitionsHandler,
    SearchTimeBlockDefinitionsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity, UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TimeBlockDefinitionCreateSchema,
    TimeBlockDefinitionSchema,
    TimeBlockDefinitionUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_time_block_definition_to_schema

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=TimeBlockDefinitionSchema)
async def get_time_block_definition(
    uuid: UUID,
    handler: Annotated[
        GetTimeBlockDefinitionHandler,
        Depends(create_query_handler(GetTimeBlockDefinitionHandler)),
    ],
) -> TimeBlockDefinitionSchema:
    """Get a single time block definition by ID."""
    time_block_definition = await handler.handle(
        GetTimeBlockDefinitionQuery(time_block_definition_id=uuid)
    )
    return map_time_block_definition_to_schema(time_block_definition)


@router.post("/", response_model=PagedResponseSchema[TimeBlockDefinitionSchema])
async def search_time_block_definitions(
    query: QuerySchema[value_objects.TimeBlockDefinitionQuery],
    handler: Annotated[
        SearchTimeBlockDefinitionsHandler,
        Depends(create_query_handler(SearchTimeBlockDefinitionsHandler)),
    ],
) -> PagedResponseSchema[TimeBlockDefinitionSchema]:
    """Search time block definitions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.TimeBlockDefinitionQuery)
    result = await handler.handle(
        SearchTimeBlockDefinitionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_time_block_definition_to_schema)


@router.post(
    "/create",
    response_model=TimeBlockDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_block_definition(
    time_block_definition_data: TimeBlockDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        CreateTimeBlockDefinitionHandler,
        Depends(create_command_handler(CreateTimeBlockDefinitionHandler)),
    ],
) -> TimeBlockDefinitionSchema:
    """Create a new time block definition."""
    time_block_definition = TimeBlockDefinitionEntity(
        user_id=user.id,
        name=time_block_definition_data.name,
        description=time_block_definition_data.description,
        type=time_block_definition_data.type,
        category=time_block_definition_data.category,
    )
    created = await handler.handle(
        CreateTimeBlockDefinitionCommand(time_block_definition=time_block_definition)
    )
    return map_time_block_definition_to_schema(created)


@router.put("/{uuid}", response_model=TimeBlockDefinitionSchema)
async def update_time_block_definition(
    uuid: UUID,
    update_data: TimeBlockDefinitionUpdateSchema,
    handler: Annotated[
        UpdateTimeBlockDefinitionHandler,
        Depends(create_command_handler(UpdateTimeBlockDefinitionHandler)),
    ],
) -> TimeBlockDefinitionSchema:
    """Update an existing time block definition."""
    update_object = value_objects.TimeBlockDefinitionUpdateObject(
        name=update_data.name,
        description=update_data.description,
        type=update_data.type,
        category=update_data.category,
    )
    updated = await handler.handle(
        UpdateTimeBlockDefinitionCommand(
            time_block_definition_id=uuid, update_data=update_object
        )
    )
    return map_time_block_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_block_definition(
    uuid: UUID,
    handler: Annotated[
        DeleteTimeBlockDefinitionHandler,
        Depends(create_command_handler(DeleteTimeBlockDefinitionHandler)),
    ],
) -> None:
    """Delete a time block definition."""
    await handler.handle(
        DeleteTimeBlockDefinitionCommand(time_block_definition_id=uuid)
    )
