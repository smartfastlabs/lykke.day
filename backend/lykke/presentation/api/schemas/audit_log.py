"""AuditLog API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from .base import BaseSchema


class AuditLogSchema(BaseSchema):
    """Schema for AuditLog entity."""

    id: UUID
    user_id: UUID
    activity_type: str
    occurred_at: datetime
    entity_id: UUID | None
    entity_type: str | None
    meta: dict[str, Any]
