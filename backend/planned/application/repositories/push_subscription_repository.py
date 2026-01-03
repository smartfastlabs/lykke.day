"""Protocol for PushSubscriptionRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.infrastructure import data_objects


class PushSubscriptionRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[data_objects.PushSubscription]):
    """Read-only protocol defining the interface for push subscription repositories."""


class PushSubscriptionRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[data_objects.PushSubscription]):
    """Read-write protocol defining the interface for push subscription repositories."""

