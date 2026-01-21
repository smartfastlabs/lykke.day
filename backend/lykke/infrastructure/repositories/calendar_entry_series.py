from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntrySeriesEntity
from lykke.infrastructure.database.tables import calendar_entry_series_tbl
from lykke.infrastructure.repositories.base import BaseQuery, UserScopedBaseRepository

CalendarEntrySeriesQuery = value_objects.CalendarEntrySeriesQuery


class CalendarEntrySeriesRepository(
    UserScopedBaseRepository[CalendarEntrySeriesEntity, CalendarEntrySeriesQuery]
):
    Object = CalendarEntrySeriesEntity
    table = calendar_entry_series_tbl
    QueryClass = CalendarEntrySeriesQuery

    def build_query(self, query: BaseQuery) -> Select[tuple]:
        stmt = super().build_query(query)  # type: ignore[arg-type]

        if isinstance(query, CalendarEntrySeriesQuery):
            if query.calendar_id is not None:
                stmt = stmt.where(self.table.c.calendar_id == query.calendar_id)
            if query.platform_id is not None:
                stmt = stmt.where(self.table.c.platform_id == query.platform_id)

        return stmt

    @staticmethod
    def entity_to_row(series: CalendarEntrySeriesEntity) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": series.id,
            "user_id": series.user_id,
            "calendar_id": series.calendar_id,
            "name": series.name,
            "platform_id": series.platform_id,
            "platform": series.platform,
            "frequency": series.frequency.value,
            "event_category": (
                series.event_category.value if series.event_category else None
            ),
            "recurrence": series.recurrence or None,
            "starts_at": series.starts_at,
            "ends_at": series.ends_at,
            "created_at": series.created_at,
            "updated_at": series.updated_at,
        }
        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> CalendarEntrySeriesEntity:
        data = dict(row)
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = value_objects.TaskFrequency(data["frequency"])
        if "event_category" in data and isinstance(data["event_category"], str):
            data["event_category"] = value_objects.EventCategory(data["event_category"])

        return CalendarEntrySeriesEntity(**data)
