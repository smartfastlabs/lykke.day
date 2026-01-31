"""Value objects for AI chatbot system."""

from enum import Enum


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Type of message (channel/direction)."""

    UNKNOWN = "UNKNOWN"
    SMS_INBOUND = "SMS_INBOUND"
    SMS_OUTBOUND = "SMS_OUTBOUND"


class FactoidType(str, Enum):
    """Type of factoid/memory stored."""

    EPISODIC = "episodic"  # Specific events or experiences
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How-to information


class FactoidCriticality(str, Enum):
    """Criticality level of a factoid."""

    NORMAL = "normal"
    IMPORTANT = "important"
    CRITICAL = "critical"


class LLMProvider(str, Enum):
    """LLM provider for generating responses."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
