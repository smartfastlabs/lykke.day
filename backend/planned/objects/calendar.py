from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseObject


class Calendar(BaseObject):
    name: str
    auth_token_uuid: UUID 
    platform_id: str 
    platform: str
    last_sync_at: datetime | None = None
