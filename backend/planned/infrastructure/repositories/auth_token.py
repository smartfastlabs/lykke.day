from planned.domain.entities import AuthToken

from .base import BaseCrudRepository


class AuthTokenRepository(BaseCrudRepository[AuthToken]):
    Object = AuthToken
    _prefix = "auth-tokens"
