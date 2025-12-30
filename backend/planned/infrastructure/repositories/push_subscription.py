from typing import Any
from uuid import UUID

from planned.domain.entities import PushSubscription

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import push_subscriptions_tbl
from .base.utils import normalize_list_fields


class PushSubscriptionRepository(UserScopedBaseRepository[PushSubscription, BaseQuery]):
    Object = PushSubscription
    table = push_subscriptions_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize PushSubscriptionRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(push_subscription: PushSubscription) -> dict[str, Any]:
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

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> PushSubscription:
        """Convert a database row dict to a PushSubscription entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, PushSubscription)
        return PushSubscription.model_validate(data, from_attributes=True)
