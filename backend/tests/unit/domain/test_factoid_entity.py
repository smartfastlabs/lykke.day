"""Unit tests for FactoidEntity domain logic."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity
from lykke.domain.events.ai_chat_events import FactoidCriticalityUpdatedEvent


@pytest.fixture
def factoid() -> FactoidEntity:
    """Create a test factoid entity."""
    return FactoidEntity(
        id=uuid4(),
        user_id=uuid4(),
        conversation_id=uuid4(),
        factoid_type=value_objects.FactoidType.EPISODIC,
        criticality=value_objects.FactoidCriticality.NORMAL,
        content="User mentioned they love hiking on weekends.",
    )


def test_factoid_creation() -> None:
    """Test creating a factoid entity."""
    user_id = uuid4()
    content = "User prefers morning meetings"
    
    factoid = FactoidEntity(
        user_id=user_id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content=content,
    )

    assert factoid.user_id == user_id
    assert factoid.conversation_id is None  # Global factoid
    assert factoid.factoid_type == value_objects.FactoidType.SEMANTIC
    assert factoid.criticality == value_objects.FactoidCriticality.NORMAL
    assert factoid.content == content
    assert factoid.ai_suggested is False
    assert factoid.user_confirmed is False
    assert factoid.access_count == 0


def test_access_updates_timestamp_and_count(factoid: FactoidEntity) -> None:
    """Test that access() updates timestamp and increments count."""
    import time

    original_time = factoid.last_accessed
    original_count = factoid.access_count

    time.sleep(0.01)
    accessed = factoid.access()

    assert accessed.last_accessed > original_time
    assert accessed.access_count == original_count + 1
    # Note: access() doesn't add domain events (internal tracking)


def test_access_multiple_times(factoid: FactoidEntity) -> None:
    """Test multiple accesses increment count correctly."""
    factoid = factoid.access()
    assert factoid.access_count == 1

    factoid = factoid.access()
    assert factoid.access_count == 2

    factoid = factoid.access()
    assert factoid.access_count == 3


def test_update_criticality_adds_event(factoid: FactoidEntity) -> None:
    """Test that update_criticality adds a domain event."""
    updated = factoid.update_criticality(
        new_criticality=value_objects.FactoidCriticality.IMPORTANT,
        user_confirmed=True,
    )

    # Should have a domain event
    assert updated.has_events()
    events = updated.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], FactoidCriticalityUpdatedEvent)

    # Check event data
    event = events[0]
    assert event.factoid_id == factoid.id
    assert event.old_criticality == value_objects.FactoidCriticality.NORMAL.value
    assert event.new_criticality == value_objects.FactoidCriticality.IMPORTANT.value
    assert event.user_confirmed is True


def test_update_criticality_changes_level(factoid: FactoidEntity) -> None:
    """Test that update_criticality changes the criticality level."""
    updated = factoid.update_criticality(
        new_criticality=value_objects.FactoidCriticality.CRITICAL
    )

    assert updated.criticality == value_objects.FactoidCriticality.CRITICAL
    assert factoid.criticality == value_objects.FactoidCriticality.NORMAL  # Original unchanged


def test_update_criticality_sets_user_confirmed(factoid: FactoidEntity) -> None:
    """Test that update_criticality sets user_confirmed flag."""
    # Without user confirmation
    updated = factoid.update_criticality(
        new_criticality=value_objects.FactoidCriticality.IMPORTANT,
        user_confirmed=False,
    )
    assert updated.user_confirmed is False

    # With user confirmation
    updated = factoid.update_criticality(
        new_criticality=value_objects.FactoidCriticality.IMPORTANT,
        user_confirmed=True,
    )
    assert updated.user_confirmed is True


def test_update_criticality_preserves_previous_confirmation(factoid: FactoidEntity) -> None:
    """Test that update_criticality preserves user_confirmed if already set."""
    # First update with user confirmation
    confirmed = factoid.update_criticality(
        new_criticality=value_objects.FactoidCriticality.IMPORTANT,
        user_confirmed=True,
    )
    assert confirmed.user_confirmed is True
    confirmed.collect_events()

    # Second update without explicit confirmation
    updated_again = confirmed.update_criticality(
        new_criticality=value_objects.FactoidCriticality.CRITICAL,
        user_confirmed=False,
    )
    # Should preserve the previous confirmation
    assert updated_again.user_confirmed is True


def test_mark_ai_suggested(factoid: FactoidEntity) -> None:
    """Test marking a factoid as AI-suggested."""
    marked = factoid.mark_ai_suggested()

    assert marked.ai_suggested is True
    assert factoid.ai_suggested is False  # Original unchanged


def test_global_vs_conversation_factoid() -> None:
    """Test distinction between global and conversation-specific factoids."""
    conversation_id = uuid4()

    # Conversation-specific factoid
    conversation_factoid = FactoidEntity(
        user_id=uuid4(),
        conversation_id=conversation_id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="User mentioned this in conversation",
    )
    assert conversation_factoid.conversation_id == conversation_id

    # Global factoid
    global_factoid = FactoidEntity(
        user_id=uuid4(),
        conversation_id=None,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="User's general preference",
    )
    assert global_factoid.conversation_id is None


def test_factoid_types() -> None:
    """Test all factoid types."""
    user_id = uuid4()

    episodic = FactoidEntity(
        user_id=user_id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="User went to Paris last summer",
    )
    assert episodic.factoid_type == value_objects.FactoidType.EPISODIC

    semantic = FactoidEntity(
        user_id=user_id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="User is allergic to peanuts",
    )
    assert semantic.factoid_type == value_objects.FactoidType.SEMANTIC

    procedural = FactoidEntity(
        user_id=user_id,
        factoid_type=value_objects.FactoidType.PROCEDURAL,
        content="User prefers step-by-step instructions",
    )
    assert procedural.factoid_type == value_objects.FactoidType.PROCEDURAL


def test_factoid_with_embedding() -> None:
    """Test factoid with vector embedding."""
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    factoid = FactoidEntity(
        user_id=uuid4(),
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Test content",
        embedding=embedding,
    )

    assert factoid.embedding == embedding


def test_factoid_immutability() -> None:
    """Test that factoid operations return new instances."""
    original = FactoidEntity(
        user_id=uuid4(),
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Original",
    )

    accessed = original.access()
    assert accessed is not original
    assert accessed.id == original.id

    suggested = original.mark_ai_suggested()
    assert suggested is not original
    assert suggested.id == original.id

    updated = original.update_criticality(value_objects.FactoidCriticality.IMPORTANT)
    assert updated is not original
    assert updated.id == original.id
