import uuid
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from .base import BaseEntityObject


class PushSubscription(BaseEntityObject):
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="createdAt",
    )

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        # Generate UUID5 based on endpoint and user_uuid for deterministic IDs
        # Only set if uuid was not explicitly provided
        if "uuid" not in self.model_fields_set:
            namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
            name = f"{self.endpoint}:{self.user_uuid}"
            self.uuid = uuid.uuid5(namespace, name)
