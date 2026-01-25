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
    BrainDumpItemCreateSchema,
    BrainDumpItemSchema,
    BrainDumpItemUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_brain_dump_item_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=BrainDumpItemSchema)
async def get_brain_dump_item(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> BrainDumpItemSchema:
    """Get a single brain dump item by ID."""
    handler = query_factory.create(GetBrainDumpHandler)
    item = await handler.handle(GetBrainDumpQuery(item_id=uuid))
    return map_brain_dump_item_to_schema(item)


@router.post("/", response_model=PagedResponseSchema[BrainDumpItemSchema])
async def search_brain_dump_items(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.BrainDumpQuery],
) -> PagedResponseSchema[BrainDumpItemSchema]:
    """Search brain dump items with pagination and optional filters."""
    handler = query_factory.create(SearchBrainDumpsHandler)
    search_query = build_search_query(query, value_objects.BrainDumpQuery)
    result = await handler.handle(SearchBrainDumpsQuery(search_query=search_query))
    return create_paged_response(result, map_brain_dump_item_to_schema)


@router.post(
    "/create",
    response_model=BrainDumpItemSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_brain_dump_item(
    item_data: BrainDumpItemCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> BrainDumpItemSchema:
    """Create a new brain dump item."""
    handler = command_factory.create(CreateBrainDumpHandler)
    item = await handler.handle(
        CreateBrainDumpCommand(date=item_data.date, text=item_data.text)
    )
    return map_brain_dump_item_to_schema(item)


@router.patch("/{uuid}", response_model=BrainDumpItemSchema)
async def update_brain_dump_item(
    uuid: UUID,
    update_data: BrainDumpItemUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> BrainDumpItemSchema:
    """Update a brain dump item's status or type."""
    get_handler = query_factory.create(GetBrainDumpHandler)
    item = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))

    if update_data.status is not None:
        status_handler = command_factory.create(UpdateBrainDumpStatusHandler)
        await status_handler.handle(
            UpdateBrainDumpStatusCommand(
                date=item.date, item_id=uuid, status=update_data.status
            )
        )

    if update_data.type is not None:
        type_handler = command_factory.create(UpdateBrainDumpTypeHandler)
        await type_handler.handle(
            UpdateBrainDumpTypeCommand(
                date=item.date, item_id=uuid, item_type=update_data.type
            )
        )

    updated = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))
    return map_brain_dump_item_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brain_dump_item(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> None:
    """Delete a brain dump item."""
    get_handler = query_factory.create(GetBrainDumpHandler)
    item = await get_handler.handle(GetBrainDumpQuery(item_id=uuid))
    handler = command_factory.create(DeleteBrainDumpHandler)
    await handler.handle(DeleteBrainDumpCommand(date=item.date, item_id=uuid))
