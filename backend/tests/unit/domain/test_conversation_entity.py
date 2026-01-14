"""Unit tests for ConversationEntity domain logic."""

from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity
from lykke.domain.events.ai_chat_events import ConversationUpdatedEvent


@pytest.fixture
def conversation() -> ConversationEntity:
    """Create a test conversation entity."""
    return ConversationEntity(
        id=uuid4(),
        user_id=uuid4(),
        bot_personality_id=uuid4(),
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
    )


def test_update_last_message_time_adds_event(conversation: ConversationEntity) -> None:
    """Test that update_last_message_time adds a domain event."""
    updated = conversation.update_last_message_time()

    # Should have a domain event
    assert updated.has_events()
    events = updated.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ConversationUpdatedEvent)


def test_update_last_message_time_updates_timestamp(
    conversation: ConversationEntity,
) -> None:
    """Test that update_last_message_time actually updates the timestamp."""
    import time

    original_time = conversation.last_message_at
    time.sleep(0.01)  # Small delay to ensure timestamp difference
    updated = conversation.update_last_message_time()

    assert updated.last_message_at > original_time


def test_archive_adds_event(conversation: ConversationEntity) -> None:
    """Test that archive adds a domain event."""
    archived = conversation.archive()

    # Should have a domain event
    assert archived.has_events()
    events = archived.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ConversationUpdatedEvent)

    # Should update status
    assert archived.status == value_objects.ConversationStatus.ARCHIVED


def test_archive_preserves_other_fields(conversation: ConversationEntity) -> None:
    """Test that archive only changes status field."""
    archived = conversation.archive()

    assert archived.id == conversation.id
    assert archived.user_id == conversation.user_id
    assert archived.bot_personality_id == conversation.bot_personality_id
    assert archived.channel == conversation.channel
    assert archived.llm_provider == conversation.llm_provider


def test_pause_adds_event(conversation: ConversationEntity) -> None:
    """Test that pause adds a domain event."""
    paused = conversation.pause()

    # Should have a domain event
    assert paused.has_events()
    events = paused.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ConversationUpdatedEvent)

    # Should update status
    assert paused.status == value_objects.ConversationStatus.PAUSED


def test_resume_adds_event(conversation: ConversationEntity) -> None:
    """Test that resume adds a domain event."""
    # First pause the conversation
    paused = conversation.pause()
    paused.collect_events()  # Clear events

    # Then resume
    resumed = paused.resume()

    # Should have a domain event
    assert resumed.has_events()
    events = resumed.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], ConversationUpdatedEvent)

    # Should update status
    assert resumed.status == value_objects.ConversationStatus.ACTIVE


def test_resume_from_archived(conversation: ConversationEntity) -> None:
    """Test that resume works from archived status."""
    archived = conversation.archive()
    archived.collect_events()

    resumed = archived.resume()
    assert resumed.status == value_objects.ConversationStatus.ACTIVE
    assert resumed.has_events()


def test_methods_return_new_instances(conversation: ConversationEntity) -> None:
    """Test that all methods return new instances (immutability)."""
    updated = conversation.update_last_message_time()
    assert updated is not conversation
    assert updated.id == conversation.id

    archived = conversation.archive()
    assert archived is not conversation
    assert archived.id == conversation.id

    paused = conversation.pause()
    assert paused is not conversation
    assert paused.id == conversation.id

    resumed = paused.resume()
    assert resumed is not paused
    assert resumed.id == paused.id


def test_conversation_lifecycle() -> None:
    """Test a typical conversation lifecycle with events."""
    # Create conversation
    conv = ConversationEntity(
        user_id=uuid4(),
        bot_personality_id=uuid4(),
        channel=value_objects.ConversationChannel.IN_APP,
    )

    # Update last message time
    conv = conv.update_last_message_time()
    assert conv.has_events()
    conv.collect_events()  # Simulate UoW processing

    # Pause conversation
    conv = conv.pause()
    assert conv.status == value_objects.ConversationStatus.PAUSED
    assert conv.has_events()
    conv.collect_events()

    # Resume conversation
    conv = conv.resume()
    assert conv.status == value_objects.ConversationStatus.ACTIVE
    assert conv.has_events()
    conv.collect_events()

    # Archive conversation
    conv = conv.archive()
    assert conv.status == value_objects.ConversationStatus.ARCHIVED
    assert conv.has_events()


def test_conversation_with_custom_context() -> None:
    """Test conversation with custom context data."""
    custom_context = {"user_preferences": {"tone": "friendly"}, "session_id": "abc123"}
    conv = ConversationEntity(
        user_id=uuid4(),
        bot_personality_id=uuid4(),
        channel=value_objects.ConversationChannel.SMS,
        context=custom_context,
    )

    assert conv.context == custom_context


def test_conversation_default_values() -> None:
    """Test conversation entity default values."""
    conv = ConversationEntity(
        user_id=uuid4(),
        bot_personality_id=uuid4(),
        channel=value_objects.ConversationChannel.IN_APP,
    )

    assert conv.status == value_objects.ConversationStatus.ACTIVE
    assert conv.llm_provider == value_objects.LLMProvider.ANTHROPIC
    assert conv.context == {}
    assert conv.created_at is not None
    assert conv.last_message_at is not None
