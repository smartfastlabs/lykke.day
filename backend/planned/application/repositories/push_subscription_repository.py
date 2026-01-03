"""Protocol for PushSubscriptionRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.infrastructure import data_objects


class PushSubscriptionRepositoryProtocol(CrudRepositoryProtocol[data_objects.PushSubscription]):
    """Protocol defining the interface for push subscription repositories."""
    pass

