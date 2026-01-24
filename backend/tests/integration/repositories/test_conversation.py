"""Integration tests for ConversationRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity


@pytest.mark.asyncio
async def test_get(conversation_repo, test_user, bot_personality):
    """Test getting a conversation by ID."""
    conversation = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
    )
    await conversation_repo.put(conversation)

    result = await conversation_repo.get(conversation.id)

    assert result.id == conversation.id
    assert result.user_id == test_user.id
    assert result.bot_personality_id == bot_personality.id
    assert result.channel == value_objects.ConversationChannel.IN_APP
    assert result.status == value_objects.ConversationStatus.ACTIVE
    assert result.llm_provider == value_objects.LLMProvider.ANTHROPIC


@pytest.mark.asyncio
async def test_get_not_found(conversation_repo):
    """Test getting a non-existent conversation raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await conversation_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(conversation_repo, test_user, bot_personality):
    """Test creating a new conversation."""
    conversation = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.SMS,
        status=value_objects.ConversationStatus.ACTIVE,
        llm_provider=value_objects.LLMProvider.OPENAI,
        context={"phone_number": "+1234567890"},
    )

    result = await conversation_repo.put(conversation)

    assert result.id == conversation.id
    assert result.user_id == test_user.id
    assert result.channel == value_objects.ConversationChannel.SMS
    assert result.context == {"phone_number": "+1234567890"}


@pytest.mark.asyncio
async def test_put_update(conversation_repo, test_user, bot_personality):
    """Test updating an existing conversation."""
    conversation = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
    )
    await conversation_repo.put(conversation)

    # Update the conversation
    updated = conversation.clone(status=value_objects.ConversationStatus.ARCHIVED)
    result = await conversation_repo.put(updated)

    assert result.status == value_objects.ConversationStatus.ARCHIVED

    # Verify it was saved
    retrieved = await conversation_repo.get(conversation.id)
    assert retrieved.status == value_objects.ConversationStatus.ARCHIVED


@pytest.mark.asyncio
async def test_search_by_channel(conversation_repo, test_user, bot_personality):
    """Test searching conversations by channel."""
    conversation1 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
    )
    conversation2 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.SMS,
    )
    await conversation_repo.put(conversation1)
    await conversation_repo.put(conversation2)

    results = await conversation_repo.search(
        value_objects.ConversationQuery(
            channel=value_objects.ConversationChannel.IN_APP.value
        )
    )

    assert len(results) == 1
    assert results[0].id == conversation1.id
    assert results[0].channel == value_objects.ConversationChannel.IN_APP


@pytest.mark.asyncio
async def test_search_by_status(conversation_repo, test_user, bot_personality):
    """Test searching conversations by status."""
    conversation1 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
    )
    conversation2 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ARCHIVED,
    )
    await conversation_repo.put(conversation1)
    await conversation_repo.put(conversation2)

    results = await conversation_repo.search(
        value_objects.ConversationQuery(
            status=value_objects.ConversationStatus.ACTIVE.value
        )
    )

    assert len(results) == 1
    assert results[0].id == conversation1.id


@pytest.mark.asyncio
async def test_search_by_bot_personality(conversation_repo, test_user, bot_personality):
    """Test searching conversations by bot personality."""
    other_personality_id = uuid4()
    conversation1 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
    )
    conversation2 = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=other_personality_id,
        channel=value_objects.ConversationChannel.IN_APP,
    )
    await conversation_repo.put(conversation1)
    await conversation_repo.put(conversation2)

    results = await conversation_repo.search(
        value_objects.ConversationQuery(bot_personality_id=bot_personality.id)
    )

    assert len(results) == 1
    assert results[0].id == conversation1.id


@pytest.mark.asyncio
async def test_entity_to_row_and_back(conversation_repo, test_user, bot_personality):
    """Test round-trip conversion: entity -> row -> entity."""
    original = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.SMS,
        status=value_objects.ConversationStatus.PAUSED,
        llm_provider=value_objects.LLMProvider.OPENAI,
        context={"phone_number": "+1234567890", "last_topic": "scheduling"},
        created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
        last_message_at=datetime(2025, 1, 10, 15, 30, 0, tzinfo=UTC),
    )

    # Convert to row
    row = conversation_repo.entity_to_row(original)

    # Verify row structure
    assert row["id"] == original.id
    assert row["user_id"] == test_user.id
    assert row["bot_personality_id"] == bot_personality.id
    assert row["channel"] == "sms"
    assert row["status"] == "paused"
    assert row["llm_provider"] == "openai"
    assert row["context"] == {"phone_number": "+1234567890", "last_topic": "scheduling"}

    # Convert back to entity
    restored = conversation_repo.row_to_entity(row)

    # Verify entity matches original
    assert restored.id == original.id
    assert restored.user_id == original.user_id
    assert restored.bot_personality_id == original.bot_personality_id
    assert restored.channel == original.channel
    assert restored.status == original.status
    assert restored.llm_provider == original.llm_provider
    assert restored.context == original.context
    assert restored.created_at == original.created_at
    assert restored.last_message_at == original.last_message_at


@pytest.mark.asyncio
async def test_empty_context_handling(conversation_repo, test_user, bot_personality):
    """Test that empty context is properly handled."""
    conversation = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=value_objects.ConversationChannel.IN_APP,
        context={},
    )
    await conversation_repo.put(conversation)

    retrieved = await conversation_repo.get(conversation.id)
    assert retrieved.context == {}
