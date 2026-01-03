"""Protocol for AuthTokenRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.infrastructure import data_objects


class AuthTokenRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[data_objects.AuthToken]
):
    """Read-only protocol defining the interface for auth token repositories."""


class AuthTokenRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[data_objects.AuthToken]
):
    """Read-write protocol defining the interface for auth token repositories."""
