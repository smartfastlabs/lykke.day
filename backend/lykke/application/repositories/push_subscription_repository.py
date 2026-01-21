"""Protocol for PushSubscriptionRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity


class PushSubscriptionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[PushSubscriptionEntity]
):
    """Read-only protocol defining the interface for push subscription repositories."""

    Query = value_objects.PushSubscriptionQuery


class PushSubscriptionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[PushSubscriptionEntity]
):
    """Read-write protocol defining the interface for push subscription repositories."""

    Query = value_objects.PushSubscriptionQuery
