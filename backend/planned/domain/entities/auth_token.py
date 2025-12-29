import uuid
from datetime import UTC, datetime
from uuid import UUID

from google.oauth2.credentials import Credentials
from pydantic import ConfigDict, Field

from .base import BaseEntityObject


class AuthToken(BaseEntityObject):
    model_config = ConfigDict(
        populate_by_name=True,
        validate_by_alias=False,
        validate_by_name=True,
        # frozen=True,
    )
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    platform: str
    token: str
    refresh_token: str | None = None
    token_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def google_credentials(self) -> Credentials:
        """
        Returns the credentials for Google API.
        """

        return Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
        )
