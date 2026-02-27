"""Router for Trigger CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.trigger import (
    CreateTriggerCommand,
    CreateTriggerHandler,
    DeleteTriggerCommand,
    DeleteTriggerHandler,
    UpdateTriggerCommand,
    UpdateTriggerHandler,
    UpdateTriggerTacticsCommand,
    UpdateTriggerTacticsHandler,
)
from lykke.application.queries.trigger import (
    GetTriggerHandler,
    GetTriggerQuery,
    ListTriggerTacticsHandler,
    ListTriggerTacticsQuery,
    SearchTriggersHandler,
    SearchTriggersQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import TriggerEntity, UserEntity
from lykke.infrastructure.data.default_triggers import DEFAULT_TRIGGERS
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    TacticSchema,
    TriggerCreateSchema,
    TriggerSchema,
    TriggerTacticsUpdateSchema,
    TriggerUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import (
    map_tactic_to_schema,
    map_trigger_to_schema,
)

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/defaults", response_model=list[TriggerCreateSchema])
async def list_default_triggers() -> list[TriggerCreateSchema]:
    """List default triggers available for import."""
    return [TriggerCreateSchema(**entry) for entry in DEFAULT_TRIGGERS]


@router.post(
    "/import-defaults",
    response_model=list[TriggerSchema],
    status_code=status.HTTP_201_CREATED,
)
async def import_default_triggers(
    user: Annotated[UserEntity, Depends(get_current_user)],
    query_handler: Annotated[SearchTriggersHandler, Depends(create_query_handler(SearchTriggersHandler))],
    command_handler: Annotated[CreateTriggerHandler, Depends(create_command_handler(CreateTriggerHandler))],
) -> list[TriggerSchema]:
    """Import default triggers into the user's account."""
    existing = await query_handler.handle(SearchTriggersQuery())
    existing_names = {trigger.name for trigger in existing.items}

    created: list[TriggerSchema] = []
    for entry in DEFAULT_TRIGGERS:
        if entry["name"] in existing_names:
            continue
        trigger = TriggerEntity(
            user_id=user.id,
            name=entry["name"],
            description=entry["description"],
        )
        result = await command_handler.handle(CreateTriggerCommand(trigger=trigger))
        created.append(map_trigger_to_schema(result))

    return created


@router.get("/{uuid}", response_model=TriggerSchema)
async def get_trigger(
    uuid: UUID,
    handler: Annotated[GetTriggerHandler, Depends(create_query_handler(GetTriggerHandler))],
) -> TriggerSchema:
    """Get a single trigger by ID."""
    trigger = await handler.handle(GetTriggerQuery(trigger_id=uuid))
    return map_trigger_to_schema(trigger)


@router.post("/", response_model=PagedResponseSchema[TriggerSchema])
async def search_triggers(
    handler: Annotated[SearchTriggersHandler, Depends(create_query_handler(SearchTriggersHandler))],
    query: QuerySchema[value_objects.TriggerQuery],
) -> PagedResponseSchema[TriggerSchema]:
    """Search triggers with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.TriggerQuery)
    result = await handler.handle(SearchTriggersQuery(search_query=search_query))
    return create_paged_response(result, map_trigger_to_schema)


@router.post(
    "/create",
    response_model=TriggerSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_trigger(
    trigger_data: TriggerCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[CreateTriggerHandler, Depends(create_command_handler(CreateTriggerHandler))],
) -> TriggerSchema:
    """Create a new trigger."""
    trigger = TriggerEntity(
        user_id=user.id,
        name=trigger_data.name,
        description=trigger_data.description,
    )
    created = await handler.handle(CreateTriggerCommand(trigger=trigger))
    return map_trigger_to_schema(created)


@router.put("/{uuid}", response_model=TriggerSchema)
async def update_trigger(
    uuid: UUID,
    update_data: TriggerUpdateSchema,
    handler: Annotated[UpdateTriggerHandler, Depends(create_command_handler(UpdateTriggerHandler))],
) -> TriggerSchema:
    """Update a trigger."""
    update_object = value_objects.TriggerUpdateObject(
        name=update_data.name,
        description=update_data.description,
    )
    updated = await handler.handle(
        UpdateTriggerCommand(trigger_id=uuid, update_data=update_object)
    )
    return map_trigger_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    uuid: UUID,
    handler: Annotated[DeleteTriggerHandler, Depends(create_command_handler(DeleteTriggerHandler))],
) -> None:
    """Delete a trigger."""
    await handler.handle(DeleteTriggerCommand(trigger_id=uuid))


@router.get("/{uuid}/tactics", response_model=list[TacticSchema])
async def list_trigger_tactics(
    uuid: UUID,
    handler: Annotated[ListTriggerTacticsHandler, Depends(create_query_handler(ListTriggerTacticsHandler))],
) -> list[TacticSchema]:
    """List tactics linked to a trigger."""
    tactics = await handler.handle(ListTriggerTacticsQuery(trigger_id=uuid))
    return [map_tactic_to_schema(tactic) for tactic in tactics]


@router.put("/{uuid}/tactics", response_model=list[TacticSchema])
async def update_trigger_tactics(
    uuid: UUID,
    update_data: TriggerTacticsUpdateSchema,
    handler: Annotated[UpdateTriggerTacticsHandler, Depends(create_command_handler(UpdateTriggerTacticsHandler))],
) -> list[TacticSchema]:
    """Replace all tactics linked to a trigger."""
    tactics = await handler.handle(
        UpdateTriggerTacticsCommand(
            trigger_id=uuid, tactic_ids=update_data.tactic_ids
        )
    )
    return [map_tactic_to_schema(tactic) for tactic in tactics]
