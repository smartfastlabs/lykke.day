from datetime import datetime

from .base import BaseObject


class Calendar(BaseObject):
    name: str
    auth_token_id: str
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None
