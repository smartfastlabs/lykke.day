"""Router for DayTemplate CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands.day_template import (
    AddDayTemplateRoutineDefinitionCommand,
    AddDayTemplateRoutineDefinitionHandler,
    AddDayTemplateTimeBlockCommand,
    AddDayTemplateTimeBlockHandler,
    CreateDayTemplateCommand,
    CreateDayTemplateHandler,
    DeleteDayTemplateCommand,
    DeleteDayTemplateHandler,
    RemoveDayTemplateRoutineDefinitionCommand,
    RemoveDayTemplateRoutineDefinitionHandler,
    RemoveDayTemplateTimeBlockCommand,
    RemoveDayTemplateTimeBlockHandler,
    UpdateDayTemplateCommand,
    UpdateDayTemplateHandler,
)
from lykke.application.queries.day_template import (
    GetDayTemplateHandler,
    GetDayTemplateQuery,
    SearchDayTemplatesHandler,
    SearchDayTemplatesQuery,
)
from lykke.application.repositories import TimeBlockDefinitionRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.presentation.api.schemas import (
    DayTemplateCreateSchema,
    DayTemplateRoutineDefinitionCreateSchema,
    DayTemplateSchema,
    DayTemplateTimeBlockCreateSchema,
    DayTemplateUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_day_template_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.repositories import get_time_block_definition_ro_repo
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=DayTemplateSchema)
async def get_day_template(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> DayTemplateSchema:
    """Get a single day template by ID."""
    get_day_template_handler = query_factory.create(GetDayTemplateHandler)
    day_template = await get_day_template_handler.handle(
        GetDayTemplateQuery(day_template_id=uuid)
    )
    return map_day_template_to_schema(day_template)


@router.post("/", response_model=PagedResponseSchema[DayTemplateSchema])
async def search_day_templates(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.DayTemplateQuery],
) -> PagedResponseSchema[DayTemplateSchema]:
    """Search day templates with pagination and optional filters."""
    list_day_templates_handler = query_factory.create(SearchDayTemplatesHandler)
    search_query = build_search_query(query, value_objects.DayTemplateQuery)
    result = await list_day_templates_handler.handle(
        SearchDayTemplatesQuery(search_query=search_query)
    )
    return create_paged_response(result, map_day_template_to_schema)


@router.post("/create", response_model=DayTemplateSchema)
async def create_day_template(
    day_template_data: DayTemplateCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> DayTemplateSchema:
    """Create a new day template."""
    create_day_template_handler = command_factory.create(CreateDayTemplateHandler)
    # Convert time blocks from schema to value objects
    time_blocks = [
        value_objects.DayTemplateTimeBlock(
            time_block_definition_id=tb.time_block_definition_id,
            start_time=tb.start_time,
            end_time=tb.end_time,
            name=tb.name,
        )
        for tb in day_template_data.time_blocks
    ]

    day_template = DayTemplateEntity(
        user_id=user.id,
        slug=day_template_data.slug,
        start_time=day_template_data.start_time,
        end_time=day_template_data.end_time,
        icon=day_template_data.icon,
        routine_definition_ids=day_template_data.routine_definition_ids,
        time_blocks=time_blocks,
        high_level_plan=(
            value_objects.HighLevelPlan(
                title=day_template_data.high_level_plan.title,
                text=day_template_data.high_level_plan.text,
                intentions=day_template_data.high_level_plan.intentions or [],
            )
            if day_template_data.high_level_plan
            else None
        ),
    )
    created = await create_day_template_handler.handle(
        CreateDayTemplateCommand(day_template=day_template)
    )
    return map_day_template_to_schema(created)


@router.put("/{uuid}", response_model=DayTemplateSchema)
async def update_day_template(
    uuid: UUID,
    update_data: DayTemplateUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> DayTemplateSchema:
    """Update a day template."""
    update_day_template_handler = command_factory.create(UpdateDayTemplateHandler)
    # Convert schema to update object
    from lykke.domain.value_objects import DayTemplateUpdateObject

    # Convert time blocks from schema to value objects if provided
    time_blocks = None
    if update_data.time_blocks is not None:
        time_blocks = [
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=tb.time_block_definition_id,
                start_time=tb.start_time,
                end_time=tb.end_time,
                name=tb.name,
            )
            for tb in update_data.time_blocks
        ]

    update_object = DayTemplateUpdateObject(
        slug=update_data.slug,
        start_time=update_data.start_time,
        end_time=update_data.end_time,
        icon=update_data.icon,
        routine_definition_ids=update_data.routine_definition_ids,
        time_blocks=time_blocks,
        high_level_plan=(
            value_objects.HighLevelPlan(
                title=update_data.high_level_plan.title,
                text=update_data.high_level_plan.text,
                intentions=update_data.high_level_plan.intentions or [],
            )
            if update_data.high_level_plan
            else None
        ),
    )
    updated = await update_day_template_handler.handle(
        UpdateDayTemplateCommand(day_template_id=uuid, update_data=update_object)
    )
    return map_day_template_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_day_template(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a day template."""
    delete_day_template_handler = command_factory.create(DeleteDayTemplateHandler)
    await delete_day_template_handler.handle(
        DeleteDayTemplateCommand(day_template_id=uuid)
    )


@router.post(
    "/{uuid}/routine-definitions",
    response_model=DayTemplateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_day_template_routine_definition(
    uuid: UUID,
    routine_data: DayTemplateRoutineDefinitionCreateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> DayTemplateSchema:
    """Attach a routine definition to a day template."""
    add_day_template_routine_definition_handler = command_factory.create(
        AddDayTemplateRoutineDefinitionHandler
    )
    updated = await add_day_template_routine_definition_handler.handle(
        AddDayTemplateRoutineDefinitionCommand(
            day_template_id=uuid,
            routine_definition_id=routine_data.routine_definition_id,
        )
    )
    return map_day_template_to_schema(updated)


@router.delete(
    "/{uuid}/routine-definitions/{routine_definition_id}",
    response_model=DayTemplateSchema,
)
async def remove_day_template_routine_definition(
    uuid: UUID,
    routine_definition_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> DayTemplateSchema:
    """Detach a routine definition from a day template."""
    remove_day_template_routine_definition_handler = command_factory.create(
        RemoveDayTemplateRoutineDefinitionHandler
    )
    updated = await remove_day_template_routine_definition_handler.handle(
        RemoveDayTemplateRoutineDefinitionCommand(
            day_template_id=uuid,
            routine_definition_id=routine_definition_id,
        )
    )
    return map_day_template_to_schema(updated)


@router.post(
    "/{uuid}/time-blocks",
    response_model=DayTemplateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_day_template_time_block(
    uuid: UUID,
    time_block_data: DayTemplateTimeBlockCreateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    time_block_def_repo: Annotated[
        TimeBlockDefinitionRepositoryReadOnlyProtocol,
        Depends(get_time_block_definition_ro_repo),
    ],
) -> DayTemplateSchema:
    """Add a time block to a day template."""
    add_day_template_time_block_handler = command_factory.create(
        AddDayTemplateTimeBlockHandler
    )
    # Fetch the TimeBlockDefinition to get the name
    time_block_def = await time_block_def_repo.get(
        time_block_data.time_block_definition_id
    )

    time_block = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=time_block_data.time_block_definition_id,
        start_time=time_block_data.start_time,
        end_time=time_block_data.end_time,
        name=time_block_def.name,
    )
    updated = await add_day_template_time_block_handler.handle(
        AddDayTemplateTimeBlockCommand(day_template_id=uuid, time_block=time_block)
    )
    return map_day_template_to_schema(updated)


@router.delete(
    "/{uuid}/time-blocks/{time_block_definition_id}/{start_time}",
    response_model=DayTemplateSchema,
)
async def remove_day_template_time_block(
    uuid: UUID,
    time_block_definition_id: UUID,
    start_time: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> DayTemplateSchema:
    """Remove a time block from a day template."""
    from datetime import time as time_type

    # Parse the time string (format: HH:MM:SS or HH:MM)
    time_obj = time_type.fromisoformat(start_time)

    remove_day_template_time_block_handler = command_factory.create(
        RemoveDayTemplateTimeBlockHandler
    )
    updated = await remove_day_template_time_block_handler.handle(
        RemoveDayTemplateTimeBlockCommand(
            day_template_id=uuid,
            time_block_definition_id=time_block_definition_id,
            start_time=time_obj,
        )
    )
    return map_day_template_to_schema(updated)
