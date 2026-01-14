from dataclasses import asdict
from datetime import datetime, time
from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity
from lykke.domain.value_objects.task import EventCategory
from lykke.infrastructure.database.tables import calendars_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetime_utc,
    ensure_datetimes_utc,
    filter_init_false_fields,
)

from .base import UserScopedBaseRepository


def dataclass_to_json_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict, handling UUIDs, enums, datetime, and time."""
    result = asdict(obj)

    def convert_value(value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, (datetime, time)):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(item) for item in value]
        elif hasattr(value, "value"):  # Enum
            return value.value
        return value

    return {k: convert_value(v) for k, v in result.items()}


CalendarQuery = value_objects.CalendarQuery


class CalendarRepository(UserScopedBaseRepository[CalendarEntity, CalendarQuery]):
    """User-scoped calendar repository."""

    Object = CalendarEntity
    table = calendars_tbl
    QueryClass = CalendarQuery

    def build_query(self, query: CalendarQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.subscription_id is not None:
            stmt = stmt.where(
                self.table.c.sync_subscription["subscription_id"].astext
                == query.subscription_id
            )

        if query.resource_id is not None:
            stmt = stmt.where(
                self.table.c.sync_subscription["resource_id"].astext
                == query.resource_id
            )

        return stmt

    @staticmethod
    def entity_to_row(calendar: CalendarEntity) -> dict[str, Any]:
        """Convert a Calendar entity to a database row dict."""
        row: dict[str, Any] = {
            "id": calendar.id,
            "user_id": calendar.user_id,
            "name": calendar.name,
            "auth_token_id": calendar.auth_token_id,
            "platform_id": calendar.platform_id,
            "platform": calendar.platform,
            "default_event_category": (
                calendar.default_event_category.value
                if calendar.default_event_category
                else None
            ),
            "last_sync_at": calendar.last_sync_at,
            "sync_subscription_id": calendar.sync_subscription_id,
        }

        if calendar.sync_subscription:
            row["sync_subscription"] = dataclass_to_json_dict(
                calendar.sync_subscription
            )

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> CalendarEntity:
        """Convert a database row dict to a Calendar entity."""
        data = filter_init_false_fields(dict(row), CalendarEntity)

        sync_subscription = data.get("sync_subscription")
        if sync_subscription:
            sync_subscription["expiration"] = ensure_datetime_utc(
                sync_subscription.get("expiration")
            )
            data["sync_subscription"] = value_objects.SyncSubscription(
                **sync_subscription
            )

        default_category = data.get("default_event_category")
        if isinstance(default_category, str):
            data["default_event_category"] = EventCategory(default_category)

        data = ensure_datetimes_utc(data, keys=("last_sync_at",))
        return CalendarEntity(**data)
