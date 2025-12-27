from planned.domain.entities import PushSubscription

from .base import BaseCrudRepository


class PushSubscriptionRepository(BaseCrudRepository[PushSubscription]):
    Object = PushSubscription
    _prefix = "push-subscriptions"
