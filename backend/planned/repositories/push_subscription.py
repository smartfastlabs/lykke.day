from planned.objects import PushSubscription

from .base import BaseRepository


class PushSubscriptionRepository(BaseRepository[PushSubscription]):
    Object = PushSubscription
    _prefix = "push_subscriptions"
