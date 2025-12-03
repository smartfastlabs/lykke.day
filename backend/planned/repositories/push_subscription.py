from planned.objects import PushSubscription

from .base import BaseCrudRepository


class PushSubscriptionRepository(BaseCrudRepository[PushSubscription]):
    Object = PushSubscription
    _prefix = "push-subscriptions"
