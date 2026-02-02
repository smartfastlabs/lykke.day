"""Integration tests for MessageRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity


@pytest.mark.asyncio
async def test_get(message_repo, test_user):
    """Test getting a message by ID."""
    message = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.USER,
        content="Hello!",
    )
    await message_repo.put(message)

    result = await message_repo.get(message.id)

    assert result.id == message.id
    assert result.user_id == test_user.id
    assert result.role == value_objects.MessageRole.USER
    assert result.content == "Hello!"


@pytest.mark.asyncio
async def test_get_not_found(message_repo):
    """Test getting a non-existent message raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await message_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(message_repo, test_user):
    """Test creating a new message."""
    message = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.ASSISTANT,
        type=value_objects.MessageType.UNKNOWN,
        content="Hello! How can I help you today?",
        meta={"model": "claude-3-5-sonnet-20241022", "tokens": 15},
    )

    result = await message_repo.put(message)

    assert result.id == message.id
    assert result.user_id == test_user.id
    assert result.role == value_objects.MessageRole.ASSISTANT
    assert result.type == value_objects.MessageType.UNKNOWN
    assert result.content == message.content
    assert result.meta == {"model": "claude-3-5-sonnet-20241022", "tokens": 15}


@pytest.mark.asyncio
async def test_search_by_role(message_repo, test_user):
    """Test searching messages by role."""
    message1 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.USER,
        content="User message",
    )
    message2 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Assistant message",
    )
    message3 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.SYSTEM,
        content="System message",
    )
    await message_repo.put(message1)
    await message_repo.put(message2)
    await message_repo.put(message3)

    results = await message_repo.search(
        value_objects.MessageQuery(role=value_objects.MessageRole.USER.value)
    )

    assert len(results) == 1
    assert results[0].id == message1.id


@pytest.mark.asyncio
async def test_entity_to_row_and_back(message_repo, test_user):
    """Test round-trip conversion: entity -> row -> entity."""
    original = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.ASSISTANT,
        type=value_objects.MessageType.SMS_OUTBOUND,
        content="This is a test message with some content.",
        meta={
            "model": "gpt-4",
            "tokens": 25,
            "finish_reason": "stop",
            "latency_ms": 1234,
        },
        llm_run_result=value_objects.LLMRunResultSnapshot(
            current_time=datetime(2025, 1, 15, 10, 29, 0, tzinfo=UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            referenced_entities=[],
            messages=[{"role": "system", "content": "system"}],
            tools=[{"name": "no_action"}],
            tool_choice="auto",
            model_params={"temperature": 0.2},
        ),
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
    )

    row = message_repo.entity_to_row(original)

    assert row["id"] == original.id
    assert row["user_id"] == test_user.id
    assert row["role"] == "assistant"
    assert row["type"] == "SMS_OUTBOUND"
    assert row["content"] == original.content
    assert row["meta"] == original.meta
    assert isinstance(row["llm_run_result"], dict)

    restored = message_repo.row_to_entity(row)

    assert restored.id == original.id
    assert restored.user_id == original.user_id
    assert restored.role == original.role
    assert restored.type == original.type
    assert restored.content == original.content
    assert restored.meta == original.meta
    assert restored.llm_run_result is not None
    assert restored.llm_run_result.llm_provider == value_objects.LLMProvider.OPENAI
    assert restored.llm_run_result.system_prompt == "system"
    assert restored.llm_run_result.messages
    assert restored.created_at == original.created_at


@pytest.mark.asyncio
async def test_empty_meta_handling(message_repo, test_user):
    """Test that empty meta is properly handled."""
    message = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.USER,
        content="Test message",
        meta={},
    )
    await message_repo.put(message)

    retrieved = await message_repo.get(message.id)
    assert retrieved.meta == {}


@pytest.mark.asyncio
async def test_order_by_created_at(message_repo, test_user):
    """Test that messages are ordered by created_at."""
    message1 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.USER,
        content="First message",
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC),
    )
    message2 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.ASSISTANT,
        content="Second message",
        created_at=datetime(2025, 1, 1, 10, 1, 0, tzinfo=UTC),
    )
    message3 = MessageEntity(
        id=uuid4(),
        user_id=test_user.id,
        role=value_objects.MessageRole.USER,
        content="Third message",
        created_at=datetime(2025, 1, 1, 10, 2, 0, tzinfo=UTC),
    )

    await message_repo.put(message2)
    await message_repo.put(message1)
    await message_repo.put(message3)

    results = await message_repo.search(
        value_objects.MessageQuery(order_by="created_at")
    )

    assert len(results) == 3
    assert results[0].id == message1.id
    assert results[1].id == message2.id
    assert results[2].id == message3.id
