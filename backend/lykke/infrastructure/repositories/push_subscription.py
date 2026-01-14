from typing import Any

from lykke.domain import data_objects

from .base import BaseQuery, UserScopedBaseRepository
from lykke.infrastructure.database.tables import push_subscriptions_tbl


class PushSubscriptionRepository(UserScopedBaseRepository[data_objects.PushSubscription, BaseQuery]):
    Object = data_objects.PushSubscription
    table = push_subscriptions_tbl
    QueryClass = BaseQuery

    @staticmethod
    def entity_to_row(push_subscription: data_objects.PushSubscription) -> dict[str, Any]:
        """Convert a PushSubscription entity to a database row dict."""
        row: dict[str, Any] = {
            "id": push_subscription.id,
            "user_id": push_subscription.user_id,
            "device_name": push_subscription.device_name,
            "endpoint": push_subscription.endpoint,
            "p256dh": push_subscription.p256dh,
            "auth": push_subscription.auth,
            "created_at": push_subscription.created_at,
        }

        return row
