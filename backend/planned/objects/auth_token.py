import uuid
from datetime import UTC, datetime
from uuid import UUID

from google.oauth2.credentials import Credentials
from pydantic import Field

from .base import BaseObject


class AuthToken(BaseObject):
    platform: str
    token: str
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    token_uri: str | None = Field(default=None, alias="tokenUri")
    client_id: str | None = Field(default=None, alias="clientId")
    client_secret: str | None = Field(default=None, alias="clientSecret")
    scopes: list | None = Field(default=None, alias="scopes")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    uuid: UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="createdAt"
    )

    def google_credentials(self):
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
