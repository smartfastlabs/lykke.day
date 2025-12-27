"""Protocol for PushSubscriptionRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import PushSubscription


class PushSubscriptionRepositoryProtocol(CrudRepositoryProtocol[PushSubscription]):
    """Protocol defining the interface for push subscription repositories."""
    pass

