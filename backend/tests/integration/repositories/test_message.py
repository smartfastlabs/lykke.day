"""Integration tests for MessageRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity


@pytest.mark.asyncio
async def test_get(message_repo, conversation):
    """Test getting a message by ID."""
    message = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="Hello, bot!",
    )
    await message_repo.put(message)

    result = await message_repo.get(message.id)

    assert result.id == message.id
    assert result.conversation_id == conversation.id
    assert result.role == value_objects.MessageRole.USER
    assert result.content == "Hello, bot!"


@pytest.mark.asyncio
async def test_get_not_found(message_repo):
    """Test getting a non-existent message raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await message_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(message_repo, conversation):
    """Test creating a new message."""
    message = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Hello! How can I help you today?",
        meta={"model": "claude-3-5-sonnet-20241022", "tokens": 15},
    )

    result = await message_repo.put(message)

    assert result.id == message.id
    assert result.conversation_id == conversation.id
    assert result.role == value_objects.MessageRole.ASSISTANT
    assert result.content == message.content
    assert result.meta == {"model": "claude-3-5-sonnet-20241022", "tokens": 15}


@pytest.mark.asyncio
async def test_search_by_conversation(message_repo, conversation):
    """Test searching messages by conversation_id."""
    other_conversation_id = uuid4()
    message1 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="Message 1",
    )
    message2 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Message 2",
    )
    message3 = MessageEntity(
        id=uuid4(),
        conversation_id=other_conversation_id,
        role=value_objects.MessageRole.USER,
        content="Message 3",
    )
    await message_repo.put(message1)
    await message_repo.put(message2)
    await message_repo.put(message3)

    results = await message_repo.search(
        value_objects.MessageQuery(conversation_id=conversation.id)
    )

    assert len(results) == 2
    message_ids = [m.id for m in results]
    assert message1.id in message_ids
    assert message2.id in message_ids
    assert message3.id not in message_ids


@pytest.mark.asyncio
async def test_search_by_role(message_repo, conversation):
    """Test searching messages by role."""
    message1 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="User message",
    )
    message2 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Assistant message",
    )
    message3 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.SYSTEM,
        content="System message",
    )
    await message_repo.put(message1)
    await message_repo.put(message2)
    await message_repo.put(message3)

    results = await message_repo.search(
        value_objects.MessageQuery(
            conversation_id=conversation.id, role=value_objects.MessageRole.USER.value
        )
    )

    assert len(results) == 1
    assert results[0].id == message1.id


@pytest.mark.asyncio
async def test_entity_to_row_and_back(message_repo, conversation):
    """Test round-trip conversion: entity -> row -> entity."""
    original = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="This is a test message with some content.",
        meta={
            "model": "gpt-4",
            "tokens": 25,
            "finish_reason": "stop",
            "latency_ms": 1234,
        },
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
    )

    # Convert to row
    row = message_repo.entity_to_row(original)

    # Verify row structure
    assert row["id"] == original.id
    assert row["conversation_id"] == conversation.id
    assert row["role"] == "assistant"
    assert row["content"] == original.content
    assert row["meta"] == original.meta

    # Convert back to entity
    restored = message_repo.row_to_entity(row)

    # Verify entity matches original
    assert restored.id == original.id
    assert restored.conversation_id == original.conversation_id
    assert restored.role == original.role
    assert restored.content == original.content
    assert restored.meta == original.meta
    assert restored.created_at == original.created_at


@pytest.mark.asyncio
async def test_empty_meta_handling(message_repo, conversation):
    """Test that empty meta is properly handled."""
    message = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="Test message",
        meta={},
    )
    await message_repo.put(message)

    retrieved = await message_repo.get(message.id)
    assert retrieved.meta == {}


@pytest.mark.asyncio
async def test_order_by_created_at(message_repo, conversation):
    """Test that messages are ordered by created_at."""
    message1 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="First message",
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC),
    )
    message2 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Second message",
        created_at=datetime(2025, 1, 1, 10, 1, 0, tzinfo=UTC),
    )
    message3 = MessageEntity(
        id=uuid4(),
        conversation_id=conversation.id,
        role=value_objects.MessageRole.USER,
        content="Third message",
        created_at=datetime(2025, 1, 1, 10, 2, 0, tzinfo=UTC),
    )

    # Insert out of order
    await message_repo.put(message2)
    await message_repo.put(message1)
    await message_repo.put(message3)

    # Search with order_by
    results = await message_repo.search(
        value_objects.MessageQuery(
            conversation_id=conversation.id, order_by="created_at"
        )
    )

    assert len(results) == 3
    assert results[0].id == message1.id
    assert results[1].id == message2.id
    assert results[2].id == message3.id
