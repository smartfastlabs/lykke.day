import uuid
from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseEntityObject


class Calendar(BaseEntityObject):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        # Generate UUID5 based on platform and platform_id for deterministic IDs
        # Only set if id was not explicitly provided
        if "id" not in self.model_fields_set:
            namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
            name = f"{self.platform}:{self.platform_id}"
            self.id = uuid.uuid5(namespace, name)
