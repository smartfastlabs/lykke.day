from typing import Any

from planned.domain.entities import AuthToken

from .base import BaseQuery, BaseRepository
from planned.infrastructure.database.tables import auth_tokens_tbl
from .base.utils import normalize_list_fields


class AuthTokenRepository(BaseRepository[AuthToken, BaseQuery]):
    """AuthTokenRepository is NOT user-scoped - it can be used for any user's auth tokens."""

    Object = AuthToken
    table = auth_tokens_tbl
    QueryClass = BaseQuery

    def __init__(self) -> None:
        """Initialize AuthTokenRepository without user scoping."""
        super().__init__()

    @staticmethod
    def entity_to_row(auth_token: AuthToken) -> dict[str, Any]:
        """Convert an AuthToken entity to a database row dict."""
        row: dict[str, Any] = {
            "uuid": auth_token.uuid,
            "user_uuid": auth_token.user_uuid,
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

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> AuthToken:
        """Convert a database row dict to an AuthToken entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, AuthToken)
        return AuthToken.model_validate(data, from_attributes=True)
