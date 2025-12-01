from planned.objects import AuthToken

from .base import BaseCrudRepository


class AuthTokenRepository(BaseCrudRepository[AuthToken]):
    Object = AuthToken
    _prefix = "auth_tokens"
