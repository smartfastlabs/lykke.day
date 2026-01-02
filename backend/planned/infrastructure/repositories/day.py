from typing import Any
from uuid import UUID

from planned.domain import entities

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import days_tbl


class DayRepository(UserScopedBaseRepository[entities.Day, BaseQuery]):
    Object = entities.Day
    table = days_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize DayRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(day: entities.Day) -> dict[str, Any]:
        """Convert a Day entity to a database row dict."""
        row: dict[str, Any] = {
            "id": day.id,
            "user_id": day.user_id,
            "date": day.date,
            "status": day.status.value,
            "scheduled_at": day.scheduled_at,
        }

        # Handle JSONB fields
        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = day.alarm.model_dump(mode="json")

        if day.template:
            row["template"] = day.template.model_dump(mode="json")

        return row
