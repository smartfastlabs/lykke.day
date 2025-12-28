from datetime import date as dt_date
from typing import Any

from planned.domain.entities import Day

from .base import BaseCrudRepository
from .base.schema import days


class DayRepository(BaseCrudRepository[Day]):
    Object = Day
    table = days

    @staticmethod
    def entity_to_row(day: Day) -> dict[str, Any]:
        """Convert a Day entity to a database row dict."""
        row: dict[str, Any] = {
            "id": str(day.date),
            "date": day.date,
            "template_id": day.template_id,
            "status": day.status.value,
            "scheduled_at": day.scheduled_at,
        }

        # Handle JSONB fields
        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = day.alarm.model_dump()

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Day:
        """Convert a database row dict to a Day entity."""
        data = dict(row)

        # Convert id (date string) to date field, or use date field if available
        if "date" in data:
            # Use the date field directly if available
            pass
        elif "id" in data:
            # Convert id (date string) to date field
            try:
                data["date"] = dt_date.fromisoformat(data["id"])
            except (ValueError, TypeError):
                try:
                    from datetime import datetime as dt

                    data["date"] = dt.strptime(data["id"], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    raise ValueError(f"Could not parse date from id: {data['id']}")

        # Remove id since Day uses date as the identifier (id is computed from date)
        data.pop("id", None)

        return Day.model_validate(data, from_attributes=True)
