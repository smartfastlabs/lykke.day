"""Protocol for PushNotificationRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity


class PushNotificationRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[PushNotificationEntity]
):
    """Read-only protocol defining the interface for push notification repositories."""

    Query = value_objects.PushNotificationQuery


class PushNotificationRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[PushNotificationEntity]
):
    """Read-write protocol defining the interface for push notification repositories."""

    Query = value_objects.PushNotificationQuery
