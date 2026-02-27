"""Router for BrainDump CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.brain_dump import (
    CreateBrainDumpCommand,
    CreateBrainDumpHandler,
    DeleteBrainDumpCommand,
    DeleteBrainDumpHandler,
    UpdateBrainDumpStatusCommand,
    UpdateBrainDumpStatusHandler,
    UpdateBrainDumpTypeCommand,
    UpdateBrainDumpTypeHandler,
)
from lykke.application.queries.brain_dump import (
    GetBrainDumpHandler,
    GetBrainDumpQuery,
    SearchBrainDumpsHandler,
    SearchBrainDumpsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    BrainDumpCreateSchema,
    BrainDumpSchema,
    BrainDumpUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_brain_dump_to_schema

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=BrainDumpSchema)
async def get_brain_dump(
    uuid: UUID,
    handler: Annotated[GetBrainDumpHandler, Depends(create_query_handler(GetBrainDumpHandler))],
) -> BrainDumpSchema:
    """Get a single brain dump by ID."""
    item = await handler.handle(GetBrainDumpQuery(item_id=uuid))
    return map_brain_dump_to_schema(item)


@router.post("/", response_model=PagedResponseSchema[BrainDumpSchema])
async def search_brain_dumps(
    handler: Annotated[SearchBrainDumpsHandler, Depends(create_query_handler(SearchBrainDumpsHandler))],
    query: QuerySchema[value_objects.BrainDumpQuery],
) -> PagedResponseSchema[BrainDumpSchema]:
    """Search brain dumps with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.BrainDumpQuery)
    result = await handler.handle(SearchBrainDumpsQuery(search_query=search_query))
    return create_paged_response(result, map_brain_dump_to_schema)


@router.post(
    "/create",
    response_model=BrainDumpSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_brain_dump(
    item_data: BrainDumpCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[CreateBrainDumpHandler, Depends(create_command_handler(CreateBrainDumpHandler))],
) -> BrainDumpSchema:
    """Create a new brain dump."""
    item = await handler.handle(
        CreateBrainDumpCommand(date=item_data.date, text=item_data.text)
    )
    return map_brain_dump_to_schema(item)


@router.patch("/{uuid}", response_model=BrainDumpSchema)
async def update_brain_dump(
    uuid: UUID,
    update_data: BrainDumpUpdateSchema,
    get_handler: Annotated[GetBrainDumpHandler, Depends(create_query_handler(GetBrainDumpHandler))],
    status_handler: Annotated[UpdateBrainDumpStatusHandler, Depends(create_command_handler(UpdateBrainDumpStatusHandler))],
    type_handler: Annotated[UpdateBrainDumpTypeHandler, Depends(create_command_handler(UpdateBrainDumpTypeHandler))],
) -> BrainDumpSchema:
    """Update a brain dump's status or type."""
    item = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))

    if update_data.status is not None:
        await status_handler.handle(
            UpdateBrainDumpStatusCommand(
                date=item.date, item_id=uuid, status=update_data.status
            )
        )

    if update_data.type is not None:
        await type_handler.handle(
            UpdateBrainDumpTypeCommand(
                date=item.date, item_id=uuid, item_type=update_data.type
            )
        )

    updated = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))
    return map_brain_dump_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brain_dump(
    uuid: UUID,
    get_handler: Annotated[GetBrainDumpHandler, Depends(create_query_handler(GetBrainDumpHandler))],
    command_handler: Annotated[DeleteBrainDumpHandler, Depends(create_command_handler(DeleteBrainDumpHandler))],
) -> None:
    """Delete a brain dump."""
    item = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))
    await command_handler.handle(DeleteBrainDumpCommand(date=item.date, item_id=uuid))
