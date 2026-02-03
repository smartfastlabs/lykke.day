from typing import Any

from sqlalchemy.sql import Select

from lykke.domain.entities import AuthTokenEntity
from lykke.infrastructure.database.tables import auth_tokens_tbl

from .base import AuthTokenQuery, UserScopedBaseRepository


class AuthTokenRepository(UserScopedBaseRepository[AuthTokenEntity, AuthTokenQuery]):
    """AuthTokenRepository is user-scoped to the current user."""

    Object = AuthTokenEntity
    table = auth_tokens_tbl
    QueryClass = AuthTokenQuery

    def build_query(self, query: AuthTokenQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.platform is not None:
            stmt = stmt.where(self.table.c.platform == query.platform)

        return stmt

    @staticmethod
    def entity_to_row(auth_token: AuthTokenEntity) -> dict[str, Any]:
        """Convert an AuthToken entity to a database row dict."""
        row: dict[str, Any] = {
            "id": auth_token.id,
            "user_id": auth_token.user_id,
            "platform": auth_token.platform,
            "token": auth_token.token,
            "refresh_token": auth_token.refresh_token,
            "token_uri": auth_token.token_uri,
            "client_id": auth_token.client_id,
            "client_secret": auth_token.client_secret,
            "expires_at": auth_token.expires_at,
            "created_at": auth_token.created_at,
        }

        # Handle JSONB fields
        if auth_token.scopes:
            row["scopes"] = auth_token.scopes

        return row
