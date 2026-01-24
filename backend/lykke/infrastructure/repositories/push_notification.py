from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity
from lykke.infrastructure.database.tables import push_notifications_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc

from .base import UserScopedBaseRepository


class PushNotificationRepository(
    UserScopedBaseRepository[
        PushNotificationEntity, value_objects.PushNotificationQuery
    ]
):
    Object = PushNotificationEntity
    table = push_notifications_tbl
    QueryClass = value_objects.PushNotificationQuery

    def build_query(self, query: value_objects.PushNotificationQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt: Select[tuple] = super().build_query(query)

        if query.push_subscription_id is not None:
            stmt = stmt.where(
                self.table.c.push_subscription_ids.any(query.push_subscription_id)
            )

        if query.status is not None:
            stmt = stmt.where(self.table.c.status == query.status)

        if query.sent_after is not None:
            stmt = stmt.where(self.table.c.sent_at > query.sent_after)

        if query.sent_before is not None:
            stmt = stmt.where(self.table.c.sent_at < query.sent_before)

        if query.message_hash is not None:
            stmt = stmt.where(self.table.c.message_hash == query.message_hash)

        if query.llm_provider is not None:
            stmt = stmt.where(self.table.c.llm_provider == query.llm_provider)

        if query.triggered_by is not None:
            stmt = stmt.where(self.table.c.triggered_by == query.triggered_by)

        if query.priority is not None:
            stmt = stmt.where(self.table.c.priority == query.priority)

        # Default ordering: most recent first (descending by sent_at)
        if not query.order_by:
            stmt = stmt.order_by(None).order_by(self.table.c.sent_at.desc())

        return stmt

    @staticmethod
    def entity_to_row(push_notification: PushNotificationEntity) -> dict[str, Any]:
        """Convert a PushNotification entity to a database row dict."""
        row: dict[str, Any] = {
            "id": push_notification.id,
            "user_id": push_notification.user_id,
            "push_subscription_ids": push_notification.push_subscription_ids,
            "content": push_notification.content,
            "status": push_notification.status,
            "error_message": push_notification.error_message,
            "sent_at": push_notification.sent_at,
            "message": push_notification.message,
            "priority": push_notification.priority,
            "reason": push_notification.reason,
            "day_context_snapshot": push_notification.day_context_snapshot,
            "message_hash": push_notification.message_hash,
            "triggered_by": push_notification.triggered_by,
            "llm_provider": push_notification.llm_provider,
        }

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> PushNotificationEntity:
        """Convert a database row dict to a PushNotification entity."""
        from lykke.infrastructure.repositories.base.utils import (
            filter_init_false_fields,
        )

        data = dict(row)

        if data.get("day_context_snapshot") is None:
            data["day_context_snapshot"] = {}

        data = filter_init_false_fields(data, PushNotificationEntity)
        data = ensure_datetimes_utc(data, keys=("sent_at",))
        return PushNotificationEntity(**data)
