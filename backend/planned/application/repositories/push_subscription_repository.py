"""Protocol for PushSubscriptionRepository."""

from planned.application.repositories.base import (
    CrudRepositoryProtocol,
    ReadOnlyCrudRepositoryProtocol,
)
from planned.infrastructure import data_objects


class PushSubscriptionRepositoryReadOnlyProtocol(ReadOnlyCrudRepositoryProtocol[data_objects.PushSubscription]):
    """Read-only protocol defining the interface for push subscription repositories."""
    pass


class PushSubscriptionRepositoryReadWriteProtocol(CrudRepositoryProtocol[data_objects.PushSubscription]):
    """Read-write protocol defining the interface for push subscription repositories."""
    pass

