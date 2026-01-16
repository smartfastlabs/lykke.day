"""Router for TimeBlockDefinition CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.time_block_definition import (
    CreateTimeBlockDefinitionHandler,
    DeleteTimeBlockDefinitionHandler,
    UpdateTimeBlockDefinitionHandler,
)
from lykke.application.queries.time_block_definition import (
    GetTimeBlockDefinitionHandler,
    SearchTimeBlockDefinitionsHandler,
)
from lykke.domain import value_objects
from lykke.domain.data_objects import TimeBlockDefinition
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TimeBlockDefinitionCreateSchema,
    TimeBlockDefinitionSchema,
    TimeBlockDefinitionUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_time_block_definition_to_schema

from .dependencies.factories import get_command_handler, get_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=TimeBlockDefinitionSchema)
async def get_time_block_definition(
    uuid: UUID,
    get_time_block_definition_handler: Annotated[
        GetTimeBlockDefinitionHandler, Depends(get_query_handler(GetTimeBlockDefinitionHandler))
    ],
) -> TimeBlockDefinitionSchema:
    """Get a single time block definition by ID."""
    time_block_definition = await get_time_block_definition_handler.run(
        time_block_definition_id=uuid
    )
    return map_time_block_definition_to_schema(time_block_definition)


@router.post(
    "/", response_model=PagedResponseSchema[TimeBlockDefinitionSchema]
)
async def search_time_block_definitions(
    list_time_block_definitions_handler: Annotated[
        SearchTimeBlockDefinitionsHandler,
        Depends(get_query_handler(SearchTimeBlockDefinitionsHandler)),
    ],
    query: QuerySchema[value_objects.TimeBlockDefinitionQuery],
) -> PagedResponseSchema[TimeBlockDefinitionSchema]:
    """Search time block definitions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.TimeBlockDefinitionQuery)
    result = await list_time_block_definitions_handler.run(search_query=search_query)
    return create_paged_response(result, map_time_block_definition_to_schema)


@router.post(
    "/create",
    response_model=TimeBlockDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_block_definition(
    time_block_definition_data: TimeBlockDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_time_block_definition_handler: Annotated[
        CreateTimeBlockDefinitionHandler,
        Depends(get_command_handler(CreateTimeBlockDefinitionHandler)),
    ],
) -> TimeBlockDefinitionSchema:
    """Create a new time block definition."""
    time_block_definition = TimeBlockDefinition(
        user_id=user.id,
        name=time_block_definition_data.name,
        description=time_block_definition_data.description,
        type=time_block_definition_data.type,
        category=time_block_definition_data.category,
    )
    created = await create_time_block_definition_handler.run(
        time_block_definition=time_block_definition
    )
    return map_time_block_definition_to_schema(created)


@router.put("/{uuid}", response_model=TimeBlockDefinitionSchema)
async def update_time_block_definition(
    uuid: UUID,
    update_data: TimeBlockDefinitionUpdateSchema,
    update_time_block_definition_handler: Annotated[
        UpdateTimeBlockDefinitionHandler,
        Depends(get_command_handler(UpdateTimeBlockDefinitionHandler)),
    ],
) -> TimeBlockDefinitionSchema:
    """Update an existing time block definition."""
    update_object = value_objects.TimeBlockDefinitionUpdateObject(
        name=update_data.name,
        description=update_data.description,
        type=update_data.type,
        category=update_data.category,
    )
    updated = await update_time_block_definition_handler.run(
        time_block_definition_id=uuid,
        update_data=update_object,
    )
    return map_time_block_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_block_definition(
    uuid: UUID,
    delete_time_block_definition_handler: Annotated[
        DeleteTimeBlockDefinitionHandler,
        Depends(get_command_handler(DeleteTimeBlockDefinitionHandler)),
    ],
) -> None:
    """Delete a time block definition."""
    await delete_time_block_definition_handler.run(time_block_definition_id=uuid)

