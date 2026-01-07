from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity
from lykke.infrastructure.database.tables import calendars_tbl
from lykke.infrastructure.repositories.base.utils import filter_init_false_fields

from .base import BaseQuery, UserScopedBaseRepository


class CalendarRepository(UserScopedBaseRepository[CalendarEntity, BaseQuery]):
    Object = CalendarEntity
    table = calendars_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize CalendarRepository with user scoping."""
        super().__init__(user_id=user_id)

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
            "last_sync_at": calendar.last_sync_at,
            "sync_subscription_id": calendar.sync_subscription_id,
        }

        if calendar.sync_subscription:
            row["sync_subscription"] = calendar.sync_subscription.model_dump(mode="json")

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> CalendarEntity:
        """Convert a database row dict to a Calendar entity."""
        data = filter_init_false_fields(dict(row), CalendarEntity)

        sync_subscription = data.get("sync_subscription")
        if sync_subscription:
            data["sync_subscription"] = value_objects.SyncSubscription(**sync_subscription)

        return CalendarEntity(**data)
