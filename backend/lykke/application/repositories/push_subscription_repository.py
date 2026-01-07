"""Protocol for PushSubscriptionRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.infrastructure import data_objects


class PushSubscriptionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[data_objects.PushSubscription]
):
    """Read-only protocol defining the interface for push subscription repositories."""

    Query = value_objects.PushSubscriptionQuery


class PushSubscriptionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[data_objects.PushSubscription]
):
    """Read-write protocol defining the interface for push subscription repositories."""

    Query = value_objects.PushSubscriptionQuery
