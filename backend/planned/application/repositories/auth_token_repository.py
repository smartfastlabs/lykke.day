"""Protocol for AuthTokenRepository."""

from planned.application.repositories.base import (
    BasicCrudRepositoryProtocol,
    ReadOnlyBasicCrudRepositoryProtocol,
)
from planned.infrastructure import data_objects


class AuthTokenRepositoryReadOnlyProtocol(
    ReadOnlyBasicCrudRepositoryProtocol[data_objects.AuthToken]
):
    """Read-only protocol defining the interface for auth token repositories."""

    pass


class AuthTokenRepositoryReadWriteProtocol(
    BasicCrudRepositoryProtocol[data_objects.AuthToken]
):
    """Read-write protocol defining the interface for auth token repositories."""

    pass
