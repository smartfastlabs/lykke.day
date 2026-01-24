"""Unit tests for MessageEntity domain logic."""

from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity


@pytest.fixture
def message() -> MessageEntity:
    """Create a test message entity."""
    return MessageEntity(
        id=uuid4(),
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content="Hello, how are you today?",
    )


def test_message_creation() -> None:
    """Test creating a message entity."""
    conversation_id = uuid4()
    content = "Test message"

    message = MessageEntity(
        conversation_id=conversation_id,
        role=value_objects.MessageRole.ASSISTANT,
        content=content,
    )

    assert message.conversation_id == conversation_id
    assert message.role == value_objects.MessageRole.ASSISTANT
    assert message.content == content
    assert message.meta == {}
    assert message.created_at is not None


def test_message_with_metadata() -> None:
    """Test message with custom metadata."""
    meta_data = {
        "tokens": 150,
        "model": "claude-3-opus",
        "temperature": 0.7,
    }

    message = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.ASSISTANT,
        content="Response with metadata",
        meta=meta_data,
    )

    assert message.meta == meta_data


def test_get_content_preview_short_message(message: MessageEntity) -> None:
    """Test content preview with message shorter than max length."""
    preview = message.get_content_preview(max_length=100)
    assert preview == message.content
    assert "..." not in preview


def test_get_content_preview_long_message() -> None:
    """Test content preview with message longer than max length."""
    long_content = "A" * 200
    message = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content=long_content,
    )

    preview = message.get_content_preview(max_length=50)
    assert len(preview) == 53  # 50 chars + "..."
    assert preview.endswith("...")
    assert preview.startswith("A" * 50)


def test_get_content_preview_exact_length() -> None:
    """Test content preview when content is exactly max length."""
    content = "A" * 100
    message = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content=content,
    )

    preview = message.get_content_preview(max_length=100)
    assert preview == content
    assert "..." not in preview


def test_get_content_preview_default_length() -> None:
    """Test content preview with default max length of 100."""
    long_content = "B" * 150
    message = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content=long_content,
    )

    preview = message.get_content_preview()
    assert len(preview) == 103  # 100 chars + "..."
    assert preview.endswith("...")


def test_message_roles() -> None:
    """Test all message role types."""
    conversation_id = uuid4()

    user_message = MessageEntity(
        conversation_id=conversation_id,
        role=value_objects.MessageRole.USER,
        content="User message",
    )
    assert user_message.role == value_objects.MessageRole.USER

    assistant_message = MessageEntity(
        conversation_id=conversation_id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Assistant message",
    )
    assert assistant_message.role == value_objects.MessageRole.ASSISTANT

    system_message = MessageEntity(
        conversation_id=conversation_id,
        role=value_objects.MessageRole.SYSTEM,
        content="System message",
    )
    assert system_message.role == value_objects.MessageRole.SYSTEM


def test_message_immutability() -> None:
    """Test that message entities are immutable (via clone)."""
    original = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content="Original content",
    )

    # Clone with updated content
    updated = original.clone(content="Updated content")

    assert original.content == "Original content"
    assert updated.content == "Updated content"
    assert original.id == updated.id  # ID preserved
    assert original is not updated  # Different instances
