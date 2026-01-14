"""WebSocket message schemas for real-time communication."""

from typing import Literal
from uuid import UUID

from .audit_log import AuditLogSchema
from .base import BaseSchema
from .message import MessageSchema


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
