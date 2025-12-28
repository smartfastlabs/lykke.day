from datetime import datetime
from uuid import UUID

from .base import BaseConfigObject


class Calendar(BaseConfigObject):
    user_uuid: UUID
    name: str
    auth_token_id: str
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        self.id = f"{self.platform}:{self.platform_id}"
