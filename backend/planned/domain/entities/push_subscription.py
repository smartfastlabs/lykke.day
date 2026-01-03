import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from .base import BaseEntityObject


@dataclass(kw_only=True)
class PushSubscription(BaseEntityObject):
    user_id: UUID
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(init=False)

    def __post_init__(self) -> None:
        # Generate UUID5 based on endpoint and user_id for deterministic IDs
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{self.endpoint}:{self.user_id}"
        object.__setattr__(self, "id", uuid.uuid5(namespace, name))

