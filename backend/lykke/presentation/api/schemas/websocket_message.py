"""WebSocket message schemas for real-time communication."""

from typing import Any, Literal
from uuid import UUID

from .base import BaseSchema
from .brain_dump import BrainDumpSchema
from .calendar_entry import CalendarEntrySchema
from .day import DaySchema
from .day_context import DayContextSchema
from .message import MessageSchema
from .push_notification import PushNotificationSchema
from .routine import RoutineSchema
from .task import TaskSchema

DayContextPartKey = Literal[
    "day",
    "tasks",
    "calendar_entries",
    "routines",
    "brain_dumps",
    "push_notifications",
    "messages",
]


class DayContextPartialSchema(BaseSchema):
    """Partial day context payload for incremental sync."""

    day: DaySchema | None = None
    calendar_entries: list[CalendarEntrySchema] | None = None
    tasks: list[TaskSchema] | None = None
    routines: list[RoutineSchema] | None = None
    brain_dumps: list[BrainDumpSchema] | None = None
    push_notifications: list[PushNotificationSchema] | None = None
    messages: list[MessageSchema] | None = None


class WebSocketUserMessageSchema(BaseSchema):
    """Client → Server: User sends a message."""

    type: Literal["user_message"] = "user_message"
    content: str
    message_id: UUID | None = None  # Client can provide for idempotency


class WebSocketMessageEventSchema(BaseSchema):
    """Server → Client: Message event (message sent, received, etc)."""

    type: Literal["message_event"] = "message_event"
    message: MessageSchema


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
    since_change_stream_id: str | None = (
        None  # Redis stream id for entity change stream incremental sync
    )
    last_seen_domain_event_id: str | None = None
    partial_key: DayContextPartKey | None = None
    partial_keys: list[DayContextPartKey] | None = None


class WebSocketSubscriptionSchema(BaseSchema):
    """Client → Server: Subscribe or unsubscribe to domain event topics."""

    type: Literal["subscribe", "unsubscribe"]
    topics: list[str]


class EntityChangeSchema(BaseSchema):
    """Represents a single entity change event for current-day entities."""

    change_type: Literal["created", "updated", "deleted"]
    entity_type: str  # "task" or "calendar_entry"
    entity_id: UUID
    entity_data: (
        dict[str, Any] | None
    )  # Full entity data for created/updated, None for deleted
    entity_patch: list[dict[str, Any]] | None = None


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
    partial_context: DayContextPartialSchema | None = None
    partial_key: DayContextPartKey | None = None
    sync_complete: bool | None = None
    last_change_timestamp: str | None  # ISO format datetime - always included
    last_change_stream_id: str | None = None
    latest_domain_event_id: str | None = None


class WebSocketTopicEventSchema(BaseSchema):
    """Server → Client: Domain event message for subscribed topics."""

    type: Literal["topic_event"] = "topic_event"
    topic: str
    event: dict[str, Any]
