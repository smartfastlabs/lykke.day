from planned.domain.entities import AuthToken

from .base import BaseCrudRepository
from .base.schema import auth_tokens


class AuthTokenRepository(BaseCrudRepository[AuthToken]):
    Object = AuthToken
    table = auth_tokens
