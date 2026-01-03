from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.queries import ListEntitiesHandler
from planned.core.utils.dates import get_current_date
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity, UserEntity
from planned.presentation.api.schemas import CalendarEntrySchema
from planned.presentation.api.schemas.mappers import map_calendar_entry_to_schema

from .dependencies.services import get_list_entities_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/today", response_model=list[CalendarEntrySchema])
async def today(
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ListEntitiesHandler, Depends(get_list_entities_handler)],
) -> list[CalendarEntrySchema]:
    result: (
        list[CalendarEntryEntity]
        | value_objects.PagedQueryResponse[CalendarEntryEntity]
    ) = await handler.list_entities(
        user_id=user.id,
        repository_name="calendar_entries",
        search_query=value_objects.DateQuery(date=get_current_date()),
        paginate=False,
    )
    entries = result if isinstance(result, list) else result.items
    return [map_calendar_entry_to_schema(entry) for entry in entries]
