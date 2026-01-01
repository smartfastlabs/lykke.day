from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import AuthToken
from planned.infrastructure.database.tables import auth_tokens_tbl

from .base import AuthTokenQuery, BaseRepository


class AuthTokenRepository(BaseRepository[AuthToken, AuthTokenQuery]):
    """AuthTokenRepository is NOT user-scoped - it can be used for any user's auth tokens."""

    Object = AuthToken
    table = auth_tokens_tbl
    QueryClass = AuthTokenQuery

    def __init__(self) -> None:
        """Initialize AuthTokenRepository without user scoping."""
        super().__init__()

    def build_query(self, query: AuthTokenQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.user_id is not None:
            stmt = stmt.where(self.table.c.user_id == query.user_id)

        if query.platform is not None:
            stmt = stmt.where(self.table.c.platform == query.platform)

        return stmt

    async def get_by_user(self, user_id: UUID) -> list[AuthToken]:
        """Get all auth tokens for a user."""
        return await self.search_query(AuthTokenQuery(user_id=user_id))

    @staticmethod
    def entity_to_row(auth_token: AuthToken) -> dict[str, Any]:
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
