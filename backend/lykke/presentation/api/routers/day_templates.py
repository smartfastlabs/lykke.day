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

from .dependencies.factories import (
    create_command_handler,
    create_query_handler,
)
from .dependencies.repositories import get_time_block_definition_ro_repo
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=DayTemplateSchema)
async def get_day_template(
    uuid: UUID,
    handler: Annotated[
        GetDayTemplateHandler, Depends(create_query_handler(GetDayTemplateHandler))
    ],
) -> DayTemplateSchema:
    """Get a single day template by ID."""
    day_template = await handler.handle(GetDayTemplateQuery(day_template_id=uuid))
    return map_day_template_to_schema(day_template)


@router.post("/", response_model=PagedResponseSchema[DayTemplateSchema])
async def search_day_templates(
    query: QuerySchema[value_objects.DayTemplateQuery],
    handler: Annotated[
        SearchDayTemplatesHandler, Depends(create_query_handler(SearchDayTemplatesHandler))
    ],
) -> PagedResponseSchema[DayTemplateSchema]:
    """Search day templates with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.DayTemplateQuery)
    result = await handler.handle(
        SearchDayTemplatesQuery(search_query=search_query)
    )
    return create_paged_response(result, map_day_template_to_schema)


@router.post("/create", response_model=DayTemplateSchema)
async def create_day_template(
    day_template_data: DayTemplateCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        CreateDayTemplateHandler, Depends(create_command_handler(CreateDayTemplateHandler))
    ],
) -> DayTemplateSchema:
    """Create a new day template."""
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
    alarms = [
        value_objects.Alarm.from_dict(alarm.model_dump())
        for alarm in day_template_data.alarms
    ]

    day_template = DayTemplateEntity(
        user_id=user.id,
        slug=day_template_data.slug,
        start_time=day_template_data.start_time,
        end_time=day_template_data.end_time,
        icon=day_template_data.icon,
        routine_definition_ids=day_template_data.routine_definition_ids,
        time_blocks=time_blocks,
        alarms=alarms,
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
    created = await handler.handle(
        CreateDayTemplateCommand(day_template=day_template)
    )
    return map_day_template_to_schema(created)


@router.put("/{uuid}", response_model=DayTemplateSchema)
async def update_day_template(
    uuid: UUID,
    update_data: DayTemplateUpdateSchema,
    handler: Annotated[
        UpdateDayTemplateHandler, Depends(create_command_handler(UpdateDayTemplateHandler))
    ],
) -> DayTemplateSchema:
    """Update a day template."""
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
    alarms = None
    if update_data.alarms is not None:
        alarms = [
            value_objects.Alarm.from_dict(alarm.model_dump())
            for alarm in update_data.alarms
        ]

    update_object = DayTemplateUpdateObject(
        slug=update_data.slug,
        start_time=update_data.start_time,
        end_time=update_data.end_time,
        icon=update_data.icon,
        routine_definition_ids=update_data.routine_definition_ids,
        time_blocks=time_blocks,
        alarms=alarms,
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
    updated = await handler.handle(
        UpdateDayTemplateCommand(day_template_id=uuid, update_data=update_object)
    )
    return map_day_template_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_day_template(
    uuid: UUID,
    handler: Annotated[
        DeleteDayTemplateHandler, Depends(create_command_handler(DeleteDayTemplateHandler))
    ],
) -> None:
    """Delete a day template."""
    await handler.handle(DeleteDayTemplateCommand(day_template_id=uuid))


@router.post(
    "/{uuid}/routine-definitions",
    response_model=DayTemplateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_day_template_routine_definition(
    uuid: UUID,
    routine_data: DayTemplateRoutineDefinitionCreateSchema,
    handler: Annotated[
        AddDayTemplateRoutineDefinitionHandler,
        Depends(create_command_handler(AddDayTemplateRoutineDefinitionHandler)),
    ],
) -> DayTemplateSchema:
    """Attach a routine definition to a day template."""
    updated = await handler.handle(
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
    handler: Annotated[
        RemoveDayTemplateRoutineDefinitionHandler,
        Depends(create_command_handler(RemoveDayTemplateRoutineDefinitionHandler)),
    ],
) -> DayTemplateSchema:
    """Detach a routine definition from a day template."""
    updated = await handler.handle(
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
    handler: Annotated[
        AddDayTemplateTimeBlockHandler,
        Depends(create_command_handler(AddDayTemplateTimeBlockHandler)),
    ],
    time_block_def_repo: Annotated[
        TimeBlockDefinitionRepositoryReadOnlyProtocol,
        Depends(get_time_block_definition_ro_repo),
    ],
) -> DayTemplateSchema:
    """Add a time block to a day template."""
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
    updated = await handler.handle(
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
    handler: Annotated[
        RemoveDayTemplateTimeBlockHandler,
        Depends(create_command_handler(RemoveDayTemplateTimeBlockHandler)),
    ],
) -> DayTemplateSchema:
    """Remove a time block from a day template."""
    from datetime import time as time_type

    # Parse the time string (format: HH:MM:SS or HH:MM)
    time_obj = time_type.fromisoformat(start_time)

    updated = await handler.handle(
        RemoveDayTemplateTimeBlockCommand(
            day_template_id=uuid,
            time_block_definition_id=time_block_definition_id,
            start_time=time_obj,
        )
    )
    return map_day_template_to_schema(updated)
