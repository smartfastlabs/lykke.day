"""Router for Tactic CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.tactic import (
    CreateTacticCommand,
    CreateTacticHandler,
    DeleteTacticCommand,
    DeleteTacticHandler,
    UpdateTacticCommand,
    UpdateTacticHandler,
)
from lykke.application.queries.tactic import (
    GetTacticHandler,
    GetTacticQuery,
    SearchTacticsHandler,
    SearchTacticsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity, UserEntity
from lykke.infrastructure.data.default_tactics import DEFAULT_TACTICS
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TacticCreateSchema,
    TacticSchema,
    TacticUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_tactic_to_schema

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/defaults", response_model=list[TacticCreateSchema])
async def list_default_tactics() -> list[TacticCreateSchema]:
    """List default tactics available for import."""
    return [TacticCreateSchema(**entry) for entry in DEFAULT_TACTICS]


@router.post(
    "/import-defaults",
    response_model=list[TacticSchema],
    status_code=status.HTTP_201_CREATED,
)
async def import_default_tactics(
    user: Annotated[UserEntity, Depends(get_current_user)],
    query_handler: Annotated[SearchTacticsHandler, Depends(create_query_handler(SearchTacticsHandler))],
    command_handler: Annotated[CreateTacticHandler, Depends(create_command_handler(CreateTacticHandler))],
) -> list[TacticSchema]:
    """Import default tactics into the user's account."""
    existing = await query_handler.handle(SearchTacticsQuery())
    existing_names = {tactic.name for tactic in existing.items}

    created: list[TacticSchema] = []
    for entry in DEFAULT_TACTICS:
        if entry["name"] in existing_names:
            continue
        tactic = TacticEntity(
            user_id=user.id,
            name=entry["name"],
            description=entry["description"],
        )
        result = await command_handler.handle(CreateTacticCommand(tactic=tactic))
        created.append(map_tactic_to_schema(result))

    return created


@router.get("/{uuid}", response_model=TacticSchema)
async def get_tactic(
    uuid: UUID,
    handler: Annotated[GetTacticHandler, Depends(create_query_handler(GetTacticHandler))],
) -> TacticSchema:
    """Get a single tactic by ID."""
    tactic = await handler.handle(GetTacticQuery(tactic_id=uuid))
    return map_tactic_to_schema(tactic)


@router.post("/", response_model=PagedResponseSchema[TacticSchema])
async def search_tactics(
    handler: Annotated[SearchTacticsHandler, Depends(create_query_handler(SearchTacticsHandler))],
    query: QuerySchema[value_objects.TacticQuery],
) -> PagedResponseSchema[TacticSchema]:
    """Search tactics with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.TacticQuery)
    result = await handler.handle(SearchTacticsQuery(search_query=search_query))
    return create_paged_response(result, map_tactic_to_schema)


@router.post(
    "/create",
    response_model=TacticSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_tactic(
    tactic_data: TacticCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[CreateTacticHandler, Depends(create_command_handler(CreateTacticHandler))],
) -> TacticSchema:
    """Create a new tactic."""
    tactic = TacticEntity(
        user_id=user.id,
        name=tactic_data.name,
        description=tactic_data.description,
    )
    created = await handler.handle(CreateTacticCommand(tactic=tactic))
    return map_tactic_to_schema(created)


@router.put("/{uuid}", response_model=TacticSchema)
async def update_tactic(
    uuid: UUID,
    update_data: TacticUpdateSchema,
    handler: Annotated[UpdateTacticHandler, Depends(create_command_handler(UpdateTacticHandler))],
) -> TacticSchema:
    """Update a tactic."""
    update_object = value_objects.TacticUpdateObject(
        name=update_data.name,
        description=update_data.description,
    )
    updated = await handler.handle(
        UpdateTacticCommand(tactic_id=uuid, update_data=update_object)
    )
    return map_tactic_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tactic(
    uuid: UUID,
    handler: Annotated[DeleteTacticHandler, Depends(create_command_handler(DeleteTacticHandler))],
) -> None:
    """Delete a tactic."""
    await handler.handle(DeleteTacticCommand(tactic_id=uuid))
