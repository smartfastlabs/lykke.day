from typing import Any
from uuid import UUID

from planned.domain.entities import AuthToken

from .base import BaseQuery, BaseRepository
from .base.schema import auth_tokens
from .base.utils import normalize_list_fields


class AuthTokenRepository(BaseRepository[AuthToken, BaseQuery]):
    Object = AuthToken
    table = auth_tokens
    QueryClass = BaseQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize AuthTokenRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

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
