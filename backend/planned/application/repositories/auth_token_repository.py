"""Protocol for AuthTokenRepository."""

from planned.application.repositories.base import BasicCrudRepositoryProtocol
from planned.infrastructure import data_objects


class AuthTokenRepositoryProtocol(BasicCrudRepositoryProtocol[data_objects.AuthToken]):
    """Protocol defining the interface for auth token repositories."""
    pass

