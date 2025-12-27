"""Protocol for AuthTokenRepository."""

from planned.application.repositories.base import BasicCrudRepositoryProtocol
from planned.domain.entities import AuthToken


class AuthTokenRepositoryProtocol(BasicCrudRepositoryProtocol[AuthToken]):
    """Protocol defining the interface for auth token repositories."""
    pass

