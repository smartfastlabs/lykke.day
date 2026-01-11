"""Router for DayTemplate CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from lykke.application.commands.day_template import (
    AddDayTemplateRoutineHandler,
    AddDayTemplateTimeBlockHandler,
    CreateDayTemplateHandler,
    DeleteDayTemplateHandler,
    RemoveDayTemplateRoutineHandler,
    RemoveDayTemplateTimeBlockHandler,
    UpdateDayTemplateHandler,
)
from lykke.application.queries.day_template import (
    GetDayTemplateHandler,
    SearchDayTemplatesHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.presentation.api.schemas import (
    DayTemplateCreateSchema,
    DayTemplateRoutineCreateSchema,
    DayTemplateSchema,
    DayTemplateTimeBlockCreateSchema,
    DayTemplateUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_day_template_to_schema

from .dependencies.commands.day_template import (
    get_add_day_template_routine_handler,
    get_add_day_template_time_block_handler,
    get_create_day_template_handler,
    get_delete_day_template_handler,
    get_remove_day_template_routine_handler,
    get_remove_day_template_time_block_handler,
    get_update_day_template_handler,
)
from .dependencies.queries.day_template import (
    get_get_day_template_handler,
    get_list_day_templates_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=DayTemplateSchema)
async def get_day_template(
    uuid: UUID,
    get_day_template_handler: Annotated[
        GetDayTemplateHandler, Depends(get_get_day_template_handler)
    ],
) -> DayTemplateSchema:
    """Get a single day template by ID."""
    day_template = await get_day_template_handler.run(day_template_id=uuid)
    return map_day_template_to_schema(day_template)


@router.get("/", response_model=value_objects.PagedQueryResponse[DayTemplateSchema])
async def list_day_templates(
    list_day_templates_handler: Annotated[
        SearchDayTemplatesHandler, Depends(get_list_day_templates_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[DayTemplateSchema]:
    """List day templates with pagination."""
    result = await list_day_templates_handler.run(
        search_query=value_objects.DayTemplateQuery(limit=limit, offset=offset),
    )
    paged_response = result
    # Convert entities to schemas
    template_schemas = [map_day_template_to_schema(dt) for dt in paged_response.items]
    return value_objects.PagedQueryResponse(
        items=template_schemas,
        total=paged_response.total,
        limit=paged_response.limit,
        offset=paged_response.offset,
        has_next=paged_response.has_next,
        has_previous=paged_response.has_previous,
    )


@router.post("/", response_model=DayTemplateSchema)
async def create_day_template(
    day_template_data: DayTemplateCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_day_template_handler: Annotated[
        CreateDayTemplateHandler, Depends(get_create_day_template_handler)
    ],
) -> DayTemplateSchema:
    """Create a new day template."""
    # Convert schema to entity
    from lykke.domain.value_objects.alarm import Alarm

    alarm = None
    if day_template_data.alarm:
        alarm = Alarm(
            name=day_template_data.alarm.name,
            time=day_template_data.alarm.time,
            type=day_template_data.alarm.type,
            description=day_template_data.alarm.description,
            triggered_at=day_template_data.alarm.triggered_at,
        )

    # Convert time blocks from schema to value objects
    time_blocks = [
        value_objects.DayTemplateTimeBlock(
            time_block_definition_id=tb.time_block_definition_id,
            start_time=tb.start_time,
            end_time=tb.end_time,
        )
        for tb in day_template_data.time_blocks
    ]

    day_template = DayTemplateEntity(
        user_id=user.id,
        slug=day_template_data.slug,
        alarm=alarm,
        icon=day_template_data.icon,
        routine_ids=day_template_data.routine_ids,
        time_blocks=time_blocks,
    )
    created = await create_day_template_handler.run(day_template=day_template)
    return map_day_template_to_schema(created)


@router.put("/{uuid}", response_model=DayTemplateSchema)
async def update_day_template(
    uuid: UUID,
    update_data: DayTemplateUpdateSchema,
    update_day_template_handler: Annotated[
        UpdateDayTemplateHandler, Depends(get_update_day_template_handler)
    ],
) -> DayTemplateSchema:
    """Update a day template."""
    # Convert schema to update object
    from lykke.domain.value_objects import DayTemplateUpdateObject
    from lykke.domain.value_objects.alarm import Alarm

    alarm = None
    if update_data.alarm:
        alarm = Alarm(
            name=update_data.alarm.name,
            time=update_data.alarm.time,
            type=update_data.alarm.type,
            description=update_data.alarm.description,
            triggered_at=update_data.alarm.triggered_at,
        )

    # Convert time blocks from schema to value objects if provided
    time_blocks = None
    if update_data.time_blocks is not None:
        time_blocks = [
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=tb.time_block_definition_id,
                start_time=tb.start_time,
                end_time=tb.end_time,
            )
            for tb in update_data.time_blocks
        ]

    update_object = DayTemplateUpdateObject(
        slug=update_data.slug,
        alarm=alarm,
        icon=update_data.icon,
        routine_ids=update_data.routine_ids,
        time_blocks=time_blocks,
    )
    updated = await update_day_template_handler.run(
        day_template_id=uuid, update_data=update_object
    )
    return map_day_template_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_day_template(
    uuid: UUID,
    delete_day_template_handler: Annotated[
        DeleteDayTemplateHandler, Depends(get_delete_day_template_handler)
    ],
) -> None:
    """Delete a day template."""
    await delete_day_template_handler.run(day_template_id=uuid)


@router.post(
    "/{uuid}/routines",
    response_model=DayTemplateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_day_template_routine(
    uuid: UUID,
    routine_data: DayTemplateRoutineCreateSchema,
    add_day_template_routine_handler: Annotated[
        AddDayTemplateRoutineHandler,
        Depends(get_add_day_template_routine_handler),
    ],
) -> DayTemplateSchema:
    """Attach a routine to a day template."""
    updated = await add_day_template_routine_handler.run(
        day_template_id=uuid, routine_id=routine_data.routine_id
    )
    return map_day_template_to_schema(updated)


@router.delete(
    "/{uuid}/routines/{routine_id}",
    response_model=DayTemplateSchema,
)
async def remove_day_template_routine(
    uuid: UUID,
    routine_id: UUID,
    remove_day_template_routine_handler: Annotated[
        RemoveDayTemplateRoutineHandler,
        Depends(get_remove_day_template_routine_handler),
    ],
) -> DayTemplateSchema:
    """Detach a routine from a day template."""
    updated = await remove_day_template_routine_handler.run(
        day_template_id=uuid, routine_id=routine_id
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
    add_day_template_time_block_handler: Annotated[
        AddDayTemplateTimeBlockHandler,
        Depends(get_add_day_template_time_block_handler),
    ],
) -> DayTemplateSchema:
    """Add a time block to a day template."""
    time_block = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=time_block_data.time_block_definition_id,
        start_time=time_block_data.start_time,
        end_time=time_block_data.end_time,
    )
    updated = await add_day_template_time_block_handler.run(
        day_template_id=uuid, time_block=time_block
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
    remove_day_template_time_block_handler: Annotated[
        RemoveDayTemplateTimeBlockHandler,
        Depends(get_remove_day_template_time_block_handler),
    ],
) -> DayTemplateSchema:
    """Remove a time block from a day template."""
    from datetime import time as time_type

    # Parse the time string (format: HH:MM:SS or HH:MM)
    time_obj = time_type.fromisoformat(start_time)

    updated = await remove_day_template_time_block_handler.run(
        day_template_id=uuid,
        time_block_definition_id=time_block_definition_id,
        start_time=time_obj,
    )
    return map_day_template_to_schema(updated)
