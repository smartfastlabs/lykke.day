"""Router for DayTemplate CRUD operations."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.commands import (
    CreateEntityCommand,
    DeleteEntityCommand,
    UpdateEntityCommand,
)
from planned.application.mediator import Mediator
from planned.application.queries import GetEntityQuery, ListEntitiesQuery
from planned.domain import entities, value_objects
from planned.presentation.api import schemas
from planned.presentation.api.schemas.mappers import map_day_template_to_schema

from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=schemas.DayTemplate)
async def get_day_template(
    uuid: UUID,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayTemplate:
    """Get a single day template by ID."""
    query = GetEntityQuery[entities.DayTemplate](
        user_id=user.id,
        entity_id=uuid,
        repository_name="day_templates",
    )
    day_template = await mediator.query(query)
    return map_day_template_to_schema(day_template)


@router.get("/", response_model=value_objects.PagedQueryResponse[schemas.DayTemplate])
async def list_day_templates(
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> value_objects.PagedQueryResponse[schemas.DayTemplate]:
    """List day templates with pagination."""
    query = ListEntitiesQuery[entities.DayTemplate](
        user_id=user.id,
        repository_name="day_templates",
        limit=limit,
        offset=offset,
        paginate=True,
    )
    result = await mediator.query(query)
    paged_response = cast(
        "value_objects.PagedQueryResponse[entities.DayTemplate]", result
    )
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


@router.post("/", response_model=schemas.DayTemplate)
async def create_day_template(
    day_template_data: schemas.DayTemplate,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayTemplate:
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

    day_template = entities.DayTemplate(
        id=day_template_data.id if day_template_data.id else None,  # type: ignore[arg-type]
        user_id=user.id,
        slug=day_template_data.slug,
        alarm=alarm,
        icon=day_template_data.icon,
        routine_ids=day_template_data.routine_ids,
    )
    command = CreateEntityCommand[entities.DayTemplate](
        user_id=user.id,
        repository_name="day_templates",
        entity=day_template,
    )
    created = await mediator.execute(command)
    return map_day_template_to_schema(created)


@router.put("/{uuid}", response_model=schemas.DayTemplate)
async def update_day_template(
    uuid: UUID,
    day_template_data: schemas.DayTemplate,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> schemas.DayTemplate:
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

    day_template = entities.DayTemplate(
        id=uuid,
        user_id=user.id,
        slug=day_template_data.slug,
        alarm=alarm,
        icon=day_template_data.icon,
        routine_ids=day_template_data.routine_ids,
    )
    command = UpdateEntityCommand[entities.DayTemplate](
        user_id=user.id,
        repository_name="day_templates",
        entity_id=uuid,
        entity_data=day_template,
    )
    updated = await mediator.execute(command)
    return map_day_template_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_day_template(
    uuid: UUID,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> None:
    """Delete a day template."""
    command = DeleteEntityCommand(
        user_id=user.id,
        repository_name="day_templates",
        entity_id=uuid,
    )
    await mediator.execute(command)
