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

from .dependencies.commands.time_block_definition import (
    get_create_time_block_definition_handler,
    get_delete_time_block_definition_handler,
    get_update_time_block_definition_handler,
)
from .dependencies.queries.time_block_definition import (
    get_get_time_block_definition_handler,
    get_list_time_block_definitions_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=TimeBlockDefinitionSchema)
async def get_time_block_definition(
    uuid: UUID,
    get_time_block_definition_handler: Annotated[
        GetTimeBlockDefinitionHandler, Depends(get_get_time_block_definition_handler)
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
        Depends(get_list_time_block_definitions_handler),
    ],
    query: QuerySchema[value_objects.TimeBlockDefinitionQuery],
) -> PagedResponseSchema[TimeBlockDefinitionSchema]:
    """Search time block definitions with pagination and optional filters."""
    # Build the search query from the request
    filters = query.filters or value_objects.TimeBlockDefinitionQuery()
    search_query = value_objects.TimeBlockDefinitionQuery(
        limit=query.limit,
        offset=query.offset,
        created_before=filters.created_before,
        created_after=filters.created_after,
        order_by=filters.order_by,
        order_by_desc=filters.order_by_desc,
    )
    result = await list_time_block_definitions_handler.run(search_query=search_query)
    # Convert data objects to schemas
    time_block_definition_schemas = [
        map_time_block_definition_to_schema(tbd) for tbd in result.items
    ]
    return PagedResponseSchema(
        items=time_block_definition_schemas,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


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
        Depends(get_create_time_block_definition_handler),
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
        Depends(get_update_time_block_definition_handler),
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
        Depends(get_delete_time_block_definition_handler),
    ],
) -> None:
    """Delete a time block definition."""
    await delete_time_block_definition_handler.run(time_block_definition_id=uuid)

