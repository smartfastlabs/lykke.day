"""Protocol for UserRepository."""

from typing import Protocol

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.domain.entities import UserEntity


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

