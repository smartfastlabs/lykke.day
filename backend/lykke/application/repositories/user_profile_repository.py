"""Protocol for UserProfileRepository."""

from typing import Protocol

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities.user_profile import UserProfileEntity


class UserProfileRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[UserProfileEntity], Protocol
):
    """Read-only protocol defining the interface for user profile repositories."""

    Query: type[value_objects.UserProfileQuery] = value_objects.UserProfileQuery


class UserProfileRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[UserProfileEntity], Protocol
):
    """Read-write protocol defining the interface for user profile repositories."""

    Query: type[value_objects.UserProfileQuery] = value_objects.UserProfileQuery

