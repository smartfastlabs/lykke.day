from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseObject


class Calendar(BaseObject):
    name: str
    auth_token_uuid: UUID = Field(alias="authTokenUuid")
    platform_id: str = Field(alias="platformId")
    platform: str
    last_sync_at: datetime | None = Field(default=None, alias="lastSyncAt")
