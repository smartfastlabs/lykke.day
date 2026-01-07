"""Protocol for UserRepository."""

from typing import Protocol

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


class UserRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[UserEntity], Protocol):
    """Read-only protocol defining the interface for user repositories."""
    
    Query: type[value_objects.UserQuery] = value_objects.UserQuery
    
    async def get_by_email(self, email: str) -> UserEntity | None:
        """Get a user by email address."""
        ...


class UserRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[UserEntity], Protocol):
    """Read-write protocol defining the interface for user repositories."""
    
    Query: type[value_objects.UserQuery] = value_objects.UserQuery
    
    async def get_by_email(self, email: str) -> UserEntity | None:
        """Get a user by email address."""
        ...

