"""WebSocket message schemas for chatbot communication."""

from typing import Literal
from uuid import UUID

from .base import BaseSchema
from .message import MessageSchema


class WebSocketUserMessageSchema(BaseSchema):
    """Client → Server: User sends a message."""

    type: Literal["user_message"] = "user_message"
    content: str
    message_id: UUID | None = None  # Client can provide for idempotency


class WebSocketMessageReceivedSchema(BaseSchema):
    """Server → Client: Acknowledgment that user message was received."""

    type: Literal["message_received"] = "message_received"
    message: MessageSchema


class WebSocketAssistantMessageSchema(BaseSchema):
    """Server → Client: Complete assistant response."""

    type: Literal["assistant_message"] = "assistant_message"
    message: MessageSchema


class WebSocketErrorSchema(BaseSchema):
    """Server → Client: Error message."""

    type: Literal["error"] = "error"
    code: str
    message: str


class WebSocketConnectionAckSchema(BaseSchema):
    """Server → Client: Connection established successfully."""

    type: Literal["connection_ack"] = "connection_ack"
    conversation_id: UUID
    user_id: UUID
    bot_personality_name: str
