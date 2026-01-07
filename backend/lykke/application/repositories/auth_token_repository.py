"""Protocol for AuthTokenRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain import data_objects


class AuthTokenRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[data_objects.AuthToken]
):
    """Read-only protocol defining the interface for auth token repositories."""

    Query = value_objects.AuthTokenQuery


class AuthTokenRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[data_objects.AuthToken]
):
    """Read-write protocol defining the interface for auth token repositories."""

    Query = value_objects.AuthTokenQuery
