"""Protocol for PushSubscriptionRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain import entities


class PushSubscriptionRepositoryProtocol(CrudRepositoryProtocol[entities.PushSubscription]):
    """Protocol defining the interface for push subscription repositories."""
    pass

