"""Protocol for AuthTokenRepository."""

from planned.application.repositories.base import BasicCrudRepositoryProtocol
from planned.domain import entities


class AuthTokenRepositoryProtocol(BasicCrudRepositoryProtocol[entities.AuthToken]):
    """Protocol defining the interface for auth token repositories."""
    pass

