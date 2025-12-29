import uuid
from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseObject


class Calendar(BaseObject):
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    name: str
    auth_token_uuid: str
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        # Generate UUID5 based on platform and platform_id for deterministic IDs
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{self.platform}:{self.platform_id}"
        self.uuid = uuid.uuid5(namespace, name)
