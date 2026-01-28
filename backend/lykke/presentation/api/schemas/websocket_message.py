"""WebSocket message schemas for real-time communication."""

from typing import Any, Literal
from uuid import UUID

from .audit_log import AuditLogSchema
from .base import BaseSchema
from .day_context import DayContextSchema
from .message import MessageSchema
from .routine import RoutineSchema


class WebSocketUserMessageSchema(BaseSchema):
    """Client → Server: User sends a message."""

    type: Literal["user_message"] = "user_message"
    conversation_id: UUID
    content: str
    message_id: UUID | None = None  # Client can provide for idempotency


class WebSocketMessageEventSchema(BaseSchema):
    """Server → Client: Message event (message sent, received, etc)."""

    type: Literal["message_event"] = "message_event"
    message: MessageSchema


class WebSocketAuditLogEventSchema(BaseSchema):
    """Server → Client: AuditLog event occurred."""

    type: Literal["audit_log_event"] = "audit_log_event"
    audit_log: AuditLogSchema


class WebSocketErrorSchema(BaseSchema):
    """Server → Client: Error message."""

    type: Literal["error"] = "error"
    code: str
    message: str


class WebSocketConnectionAckSchema(BaseSchema):
    """Server → Client: Connection established successfully."""

    type: Literal["connection_ack"] = "connection_ack"
    user_id: UUID


class WebSocketSyncRequestSchema(BaseSchema):
    """Client → Server: Request full context or incremental updates since a timestamp."""

    type: Literal["sync_request"] = "sync_request"
    since_timestamp: str | None = (
        None  # ISO format datetime - if provided, only return changes since this time
    )


class WebSocketSubscriptionSchema(BaseSchema):
    """Client → Server: Subscribe or unsubscribe to domain event topics."""

    type: Literal["subscribe", "unsubscribe"]
    topics: list[str]


class EntityChangeSchema(BaseSchema):
    """Represents a single entity change from audit logs (only for entities associated with current day)."""

    change_type: Literal["created", "updated", "deleted"]
    entity_type: str  # "task" or "calendar_entry"
    entity_id: UUID
    entity_data: (
        dict[str, Any] | None
    )  # Full entity data for created/updated, None for deleted


class WebSocketSyncResponseSchema(BaseSchema):
    """Server → Client: Response with either full context or incremental changes (filtered to current day)."""

    type: Literal["sync_response"] = "sync_response"
    # Either full context (if since_timestamp was None) or incremental changes
    day_context: DayContextSchema | None = (
        None  # Full context if since_timestamp was None
    )
    changes: list[EntityChangeSchema] | None = (
        None  # Incremental changes if since_timestamp was provided (only for today's entities)
    )
    routines: list[RoutineSchema] | None = (
        None  # Routines (included in full sync response)
    )
    last_audit_log_timestamp: str | None  # ISO format datetime - always included


class WebSocketTopicEventSchema(BaseSchema):
    """Server → Client: Domain event message for subscribed topics."""

    type: Literal["topic_event"] = "topic_event"
    topic: str
    event: dict[str, Any]


class KioskNotificationSchema(BaseSchema):
    """Kiosk notification message to be read out loud."""

    message: str
    category: str  # "calendar_event", "routine", "task_reminder", "time_block_change", "other"
    message_hash: str
    created_at: str  # ISO format datetime
    triggered_by: str | None = None


class WebSocketKioskNotificationSchema(BaseSchema):
    """Server → Client: Kiosk notification event."""

    type: Literal["kiosk_notification"] = "kiosk_notification"
    notification: KioskNotificationSchema
