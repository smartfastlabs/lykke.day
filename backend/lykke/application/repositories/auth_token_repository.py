"""Protocol for AuthTokenRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity


class AuthTokenRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[AuthTokenEntity]
):
    """Read-only protocol defining the interface for auth token repositories."""

    Query = value_objects.AuthTokenQuery


class AuthTokenRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[AuthTokenEntity]
):
    """Read-write protocol defining the interface for auth token repositories."""

    Query = value_objects.AuthTokenQuery
