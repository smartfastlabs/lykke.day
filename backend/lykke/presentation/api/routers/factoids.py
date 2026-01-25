"""Router for Factoid CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.factoid import (
    CreateFactoidCommand,
    CreateFactoidHandler,
    DeleteFactoidCommand,
    DeleteFactoidHandler,
    UpdateFactoidCommand,
    UpdateFactoidHandler,
)
from lykke.application.queries.factoid import (
    GetFactoidHandler,
    GetFactoidQuery,
    SearchFactoidsHandler,
    SearchFactoidsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity, UserEntity
from lykke.presentation.api.schemas import (
    FactoidCreateSchema,
    FactoidSchema,
    FactoidUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_factoid_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=FactoidSchema)
async def get_factoid(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> FactoidSchema:
    """Get a single factoid by ID."""
    handler = query_factory.create(GetFactoidHandler)
    factoid = await handler.handle(GetFactoidQuery(factoid_id=uuid))
    return map_factoid_to_schema(factoid)


@router.post("/", response_model=PagedResponseSchema[FactoidSchema])
async def search_factoids(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.FactoidQuery],
) -> PagedResponseSchema[FactoidSchema]:
    """Search factoids with pagination and optional filters."""
    handler = query_factory.create(SearchFactoidsHandler)
    search_query = build_search_query(query, value_objects.FactoidQuery)
    result = await handler.handle(SearchFactoidsQuery(search_query=search_query))
    return create_paged_response(result, map_factoid_to_schema)


@router.post("/create", response_model=FactoidSchema)
async def create_factoid(
    factoid_data: FactoidCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> FactoidSchema:
    """Create a new factoid."""
    handler = command_factory.create(CreateFactoidHandler)
    factoid = FactoidEntity(
        user_id=user.id,
        conversation_id=factoid_data.conversation_id,
        factoid_type=factoid_data.factoid_type,
        criticality=factoid_data.criticality,
        content=factoid_data.content,
        ai_suggested=factoid_data.ai_suggested,
        user_confirmed=factoid_data.user_confirmed,
    )
    created = await handler.handle(CreateFactoidCommand(factoid=factoid))
    return map_factoid_to_schema(created)


@router.put("/{uuid}", response_model=FactoidSchema)
async def update_factoid(
    uuid: UUID,
    update_data: FactoidUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> FactoidSchema:
    """Update a factoid."""
    handler = command_factory.create(UpdateFactoidHandler)
    update_object = value_objects.FactoidUpdateObject(
        content=update_data.content,
        factoid_type=update_data.factoid_type,
        criticality=update_data.criticality,
        conversation_id=update_data.conversation_id,
        user_confirmed=update_data.user_confirmed,
    )
    updated = await handler.handle(
        UpdateFactoidCommand(factoid_id=uuid, update_data=update_object)
    )
    return map_factoid_to_schema(updated)


@router.delete("/{uuid}", status_code=204)
async def delete_factoid(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a factoid."""
    handler = command_factory.create(DeleteFactoidHandler)
    await handler.handle(DeleteFactoidCommand(factoid_id=uuid))
