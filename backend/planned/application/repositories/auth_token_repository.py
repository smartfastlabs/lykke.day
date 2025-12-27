"""Protocol for AuthTokenRepository."""

from typing import Protocol

from planned.domain.entities import AuthToken


class AuthTokenRepositoryProtocol(Protocol):
    """Protocol defining the interface for auth token repositories."""

    async def get(self, key: str) -> AuthToken:
        """Get an auth token by key."""
        ...

    async def put(self, obj: AuthToken) -> AuthToken:
        """Save or update an auth token."""
        ...

