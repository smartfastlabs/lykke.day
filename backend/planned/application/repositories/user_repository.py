"""Protocol for UserRepository."""

from typing import Protocol

from planned.application.repositories.base import BasicCrudRepositoryProtocol
from planned.domain.entities import User


class UserRepositoryProtocol(BasicCrudRepositoryProtocol[User], Protocol):
    """Protocol defining the interface for user repositories."""
    
    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        ...

    async def all(self) -> list[User]:
        """Get all users."""
        ...

