"""Protocol for UserRepository."""

from typing import Protocol

from planned.application.repositories.base import BasicCrudRepositoryProtocol
from planned.domain import entities


class UserRepositoryProtocol(BasicCrudRepositoryProtocol[entities.User], Protocol):
    """Protocol defining the interface for user repositories."""
    
    async def get_by_email(self, email: str) -> entities.User | None:
        """Get a user by email address."""
        ...

    async def all(self) -> list[entities.User]:
        """Get all users."""
        ...

