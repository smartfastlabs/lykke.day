from planned.objects import AuthToken

from .base import BaseRepository


class AuthTokenRepository(BaseRepository[AuthToken]):
    Object = AuthToken
    _prefix = "auth_tokens"
