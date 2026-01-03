"""Router for DayTemplate CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands.day_template import (
    CreateDayTemplateHandler,
    DeleteDayTemplateHandler,
    UpdateDayTemplateHandler,
)
from planned.application.queries.day_template import (
    GetDayTemplateHandler,
    ListDayTemplatesHandler,
)
from planned.domain import value_objects
from planned.domain.entities import DayTemplateEntity, UserEntity
from planned.presentation.api.schemas import DayTemplateSchema
from planned.presentation.api.schemas.mappers import map_day_template_to_schema

from .dependencies.services import (
    get_create_day_template_handler,
    get_delete_day_template_handler,
    get_get_day_template_handler,
    get_list_day_templates_handler,
    get_update_day_template_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=DayTemplateSchema)
async def get_day_template(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[GetDayTemplateHandler, Depends(get_get_day_template_handler)],
) -> DayTemplateSchema:
    """Get a single day template by ID."""
    day_template = await handler.get_day_template(user_id=user.id, day_template_id=uuid)
    return map_day_template_to_schema(day_template)


@router.get("/", response_model=value_objects.PagedQueryResponse[DayTemplateSchema])
async def list_day_templates(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        ListDayTemplatesHandler, Depends(get_list_day_templates_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[DayTemplateSchema]:
    """List day templates with pagination."""
    result = await handler.list_day_templates(
        user_id=user.id,
        limit=limit,
        offset=offset,
        paginate=True,
    )
    paged_response = cast("value_objects.PagedQueryResponse[DayTemplateEntity]", result)
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
    day_template_data: DayTemplateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        CreateDayTemplateHandler, Depends(get_create_day_template_handler)
    ],
) -> DayTemplateSchema:
    """Create a new day template."""
    # Convert schema to entity
    from planned.domain.value_objects.alarm import Alarm

    alarm = None
    if day_template_data.alarm:
        alarm = Alarm(
            name=day_template_data.alarm.name,
            time=day_template_data.alarm.time,
            type=day_template_data.alarm.type,
            description=day_template_data.alarm.description,
            triggered_at=day_template_data.alarm.triggered_at,
        )

    day_template = DayTemplateEntity(
        id=day_template_data.id if day_template_data.id else None,  # type: ignore[arg-type]
        user_id=user.id,
        slug=day_template_data.slug,
        alarm=alarm,
        icon=day_template_data.icon,
        routine_ids=day_template_data.routine_ids,
    )
    created = await handler.create_day_template(
        user_id=user.id, day_template=day_template
    )
    return map_day_template_to_schema(created)


@router.put("/{uuid}", response_model=DayTemplateSchema)
async def update_day_template(
    uuid: UUID,
    day_template_data: DayTemplateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        UpdateDayTemplateHandler, Depends(get_update_day_template_handler)
    ],
) -> DayTemplateSchema:
    """Update a day template."""
    # Convert schema to entity
    from planned.domain.value_objects.alarm import Alarm

    alarm = None
    if day_template_data.alarm:
        alarm = Alarm(
            name=day_template_data.alarm.name,
            time=day_template_data.alarm.time,
            type=day_template_data.alarm.type,
            description=day_template_data.alarm.description,
            triggered_at=day_template_data.alarm.triggered_at,
        )

    day_template = DayTemplateEntity(
        id=uuid,
        user_id=user.id,
        slug=day_template_data.slug,
        alarm=alarm,
        icon=day_template_data.icon,
        routine_ids=day_template_data.routine_ids,
    )
    updated = await handler.update_day_template(
        user_id=user.id, day_template_id=uuid, day_template_data=day_template
    )
    return map_day_template_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_day_template(
    uuid: UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[
        DeleteDayTemplateHandler, Depends(get_delete_day_template_handler)
    ],
) -> None:
    """Delete a day template."""
    await handler.delete_day_template(user_id=user.id, day_template_id=uuid)
