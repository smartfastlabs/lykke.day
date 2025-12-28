from typing import Any

from planned.domain.entities import PushSubscription

from .base import BaseCrudRepository
from .base.schema import push_subscriptions
from .base.utils import normalize_list_fields


class PushSubscriptionRepository(BaseCrudRepository[PushSubscription]):
    Object = PushSubscription
    table = push_subscriptions

    @staticmethod
    def entity_to_row(push_subscription: PushSubscription) -> dict[str, Any]:
        """Convert a PushSubscription entity to a database row dict."""
        row: dict[str, Any] = {
            "id": push_subscription.id,
            "device_name": push_subscription.device_name,
            "endpoint": push_subscription.endpoint,
            "p256dh": push_subscription.p256dh,
            "auth": push_subscription.auth,
            "uuid": push_subscription.uuid,
            "created_at": push_subscription.created_at,
        }

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> PushSubscription:
        """Convert a database row dict to a PushSubscription entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, PushSubscription)
        return PushSubscription.model_validate(data, from_attributes=True)
