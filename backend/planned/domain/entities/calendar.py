import uuid
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from .base import BaseEntityObject


@dataclass(kw_only=True)
class Calendar(BaseEntityObject):
    user_id: UUID
    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None
    id: UUID = field(init=False)

    def __post_init__(self) -> None:
        # Generate UUID5 based on platform and platform_id for deterministic IDs
        # Check if id was explicitly set by checking if it's the default uuid4 value
        # Since id is init=False, we always need to generate it
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{self.platform}:{self.platform_id}"
        object.__setattr__(self, "id", uuid.uuid5(namespace, name))
