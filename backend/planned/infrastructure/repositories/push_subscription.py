from planned.domain.entities import PushSubscription

from .base import BaseCrudRepository
from .base.schema import push_subscriptions


class PushSubscriptionRepository(BaseCrudRepository[PushSubscription]):
    Object = PushSubscription
    table = push_subscriptions
