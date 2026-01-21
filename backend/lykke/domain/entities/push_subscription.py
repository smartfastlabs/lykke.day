import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from lykke.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class PushSubscriptionEntity(BaseEntityObject):
    user_id: UUID
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Generate a deterministic UUID5 based on endpoint and user_id."""
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.day")
            name = f"{self.endpoint}:{self.user_id}"
            generated_id = uuid.uuid5(namespace, name)
            object.__setattr__(self, "id", generated_id)
