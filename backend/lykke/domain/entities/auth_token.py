from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lykke.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class AuthTokenEntity(BaseEntityObject):
    user_id: UUID
    platform: str
    token: str
    refresh_token: str | None = None
    token_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[Any] | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def google_credentials(self) -> Any:
        """Build Google credentials from token fields."""
        from google.oauth2.credentials import Credentials

        return Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
        )
