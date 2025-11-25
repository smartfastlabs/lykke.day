import uuid
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from .base import BaseObject


class PushSubscription(BaseObject):
    endpoint: str
    p256dh: str
    auth: str
    uuid: UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="createdAt",
    )
