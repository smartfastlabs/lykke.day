"""Protocol for UserCheckInRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity


class UserCheckInRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[UserCheckInEntity]
):
    """Read-only protocol for user check-in repositories."""

    Query = value_objects.UserCheckInQuery


class UserCheckInRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[UserCheckInEntity]
):
    """Read-write protocol for user check-in repositories."""

    Query = value_objects.UserCheckInQuery
