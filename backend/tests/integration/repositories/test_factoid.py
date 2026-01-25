"""Integration tests for FactoidRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity


@pytest.mark.asyncio
async def test_get(factoid_repo, test_user, conversation):
    """Test getting a factoid by ID."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        criticality=value_objects.FactoidCriticality.NORMAL,
        content="User prefers morning workouts.",
    )
    await factoid_repo.put(factoid)

    result = await factoid_repo.get(factoid.id)

    assert result.id == factoid.id
    assert result.user_id == test_user.id
    assert result.content == "User prefers morning workouts."


@pytest.mark.asyncio
async def test_get_not_found(factoid_repo):
    """Test getting a non-existent factoid raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await factoid_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(factoid_repo, test_user, conversation):
    """Test creating a new factoid."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.IMPORTANT,
        content="User has a cat named Whiskers.",
        ai_suggested=True,
        meta={"source": "conversation", "confidence": 0.95},
    )

    result = await factoid_repo.put(factoid)

    assert result.id == factoid.id
    assert result.factoid_type == value_objects.FactoidType.SEMANTIC
    assert result.criticality == value_objects.FactoidCriticality.IMPORTANT
    assert result.ai_suggested is True
    assert result.meta == {"source": "conversation", "confidence": 0.95}


@pytest.mark.asyncio
async def test_global_factoid(factoid_repo, test_user):
    """Test creating a global factoid (no conversation_id)."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=None,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.CRITICAL,
        content="User is allergic to peanuts.",
    )
    await factoid_repo.put(factoid)

    result = await factoid_repo.get(factoid.id)
    assert result.is_global()
    assert result.conversation_id is None


@pytest.mark.asyncio
async def test_update_criticality(factoid_repo, test_user, conversation):
    """Test updating factoid criticality."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        criticality=value_objects.FactoidCriticality.NORMAL,
        content="User mentioned they like coffee.",
    )
    await factoid_repo.put(factoid)

    # Update criticality
    updated = factoid.update_criticality(
        value_objects.FactoidCriticality.IMPORTANT, user_confirmed=True
    )
    result = await factoid_repo.put(updated)

    assert result.criticality == value_objects.FactoidCriticality.IMPORTANT
    assert result.user_confirmed is True


@pytest.mark.asyncio
async def test_access_tracking(factoid_repo, test_user, conversation):
    """Test factoid access tracking."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.PROCEDURAL,
        content="User's preferred meditation technique is box breathing.",
        access_count=0,
    )
    await factoid_repo.put(factoid)

    # Access the factoid
    accessed = factoid.access()
    await factoid_repo.put(accessed)

    result = await factoid_repo.get(factoid.id)
    assert result.access_count == 1


@pytest.mark.asyncio
async def test_search_by_conversation(
    factoid_repo, test_user, conversation, create_conversation
):
    """Test searching factoids by conversation_id."""
    other_conversation = await create_conversation(
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
    )
    factoid1 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="Factoid 1",
    )
    factoid2 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Factoid 2",
    )
    factoid3 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=other_conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="Factoid 3",
    )
    await factoid_repo.put(factoid1)
    await factoid_repo.put(factoid2)
    await factoid_repo.put(factoid3)

    results = await factoid_repo.search(
        value_objects.FactoidQuery(conversation_id=conversation.id)
    )

    assert len(results) == 2
    factoid_ids = [f.id for f in results]
    assert factoid1.id in factoid_ids
    assert factoid2.id in factoid_ids


@pytest.mark.asyncio
async def test_search_by_type(factoid_repo, test_user, conversation):
    """Test searching factoids by factoid_type."""
    factoid1 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="Episodic memory",
    )
    factoid2 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Semantic memory",
    )
    await factoid_repo.put(factoid1)
    await factoid_repo.put(factoid2)

    results = await factoid_repo.search(
        value_objects.FactoidQuery(
            factoid_type=value_objects.FactoidType.EPISODIC.value
        )
    )

    assert len(results) == 1
    assert results[0].id == factoid1.id


@pytest.mark.asyncio
async def test_search_by_criticality(factoid_repo, test_user, conversation):
    """Test searching factoids by criticality."""
    factoid1 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.CRITICAL,
        content="Critical information",
    )
    factoid2 = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.NORMAL,
        content="Normal information",
    )
    await factoid_repo.put(factoid1)
    await factoid_repo.put(factoid2)

    results = await factoid_repo.search(
        value_objects.FactoidQuery(
            criticality=value_objects.FactoidCriticality.CRITICAL.value
        )
    )

    assert len(results) == 1
    assert results[0].id == factoid1.id


@pytest.mark.asyncio
async def test_search_global_factoids(factoid_repo, test_user, conversation):
    """Test searching for global vs conversation-specific factoids."""
    global_factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=None,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Global fact",
    )
    conversation_factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        content="Conversation-specific fact",
    )
    await factoid_repo.put(global_factoid)
    await factoid_repo.put(conversation_factoid)

    # Search for global factoids only
    global_results = await factoid_repo.search(
        value_objects.FactoidQuery(is_global=True)
    )
    assert len(global_results) == 1
    assert global_results[0].id == global_factoid.id

    # Search for conversation-specific factoids only
    conversation_results = await factoid_repo.search(
        value_objects.FactoidQuery(is_global=False)
    )
    assert len(conversation_results) == 1
    assert conversation_results[0].id == conversation_factoid.id


@pytest.mark.asyncio
async def test_factoid_with_embedding(factoid_repo, test_user, conversation):
    """Test factoid with vector embedding."""
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 307  # 1535 dimensions (example)
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Factoid with embedding",
        embedding=embedding,
    )
    await factoid_repo.put(factoid)

    result = await factoid_repo.get(factoid.id)
    assert result.embedding == embedding


@pytest.mark.asyncio
async def test_entity_to_row_and_back(factoid_repo, test_user, conversation):
    """Test round-trip conversion: entity -> row -> entity."""
    original = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.PROCEDURAL,
        criticality=value_objects.FactoidCriticality.IMPORTANT,
        content="User's morning routine: wake at 6am, meditate for 10 minutes, then breakfast.",
        embedding=[0.1, 0.2, 0.3],
        ai_suggested=True,
        user_confirmed=False,
        last_accessed=datetime(2025, 1, 25, 8, 30, 0, tzinfo=UTC),
        access_count=5,
        meta={"source": "explicit_statement", "session_id": "abc123"},
        created_at=datetime(2025, 1, 20, 14, 0, 0, tzinfo=UTC),
    )

    # Convert to row
    row = factoid_repo.entity_to_row(original)

    # Verify row structure
    assert row["id"] == original.id
    assert row["user_id"] == test_user.id
    assert row["conversation_id"] == conversation.id
    assert row["factoid_type"] == "procedural"
    assert row["criticality"] == "important"
    assert row["content"] == original.content
    assert row["embedding"] == [0.1, 0.2, 0.3]
    assert row["ai_suggested"] == "true"
    assert row["user_confirmed"] == "false"
    assert row["access_count"] == 5
    assert row["meta"] == {"source": "explicit_statement", "session_id": "abc123"}

    # Convert back to entity
    restored = factoid_repo.row_to_entity(row)

    # Verify entity matches original
    assert restored.id == original.id
    assert restored.user_id == original.user_id
    assert restored.conversation_id == original.conversation_id
    assert restored.factoid_type == original.factoid_type
    assert restored.criticality == original.criticality
    assert restored.content == original.content
    assert restored.embedding == original.embedding
    assert restored.ai_suggested == original.ai_suggested
    assert restored.user_confirmed == original.user_confirmed
    assert restored.last_accessed == original.last_accessed
    assert restored.access_count == original.access_count
    assert restored.meta == original.meta
    assert restored.created_at == original.created_at


@pytest.mark.asyncio
async def test_boolean_string_conversion(factoid_repo, test_user, conversation):
    """Test that boolean fields are properly converted to/from strings."""
    factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Test boolean conversion",
        ai_suggested=True,
        user_confirmed=False,
    )
    await factoid_repo.put(factoid)

    retrieved = await factoid_repo.get(factoid.id)
    assert retrieved.ai_suggested is True
    assert retrieved.user_confirmed is False


@pytest.mark.asyncio
async def test_is_important_or_critical_method(factoid_repo, test_user, conversation):
    """Test the is_important_or_critical helper method."""
    normal_factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.EPISODIC,
        criticality=value_objects.FactoidCriticality.NORMAL,
        content="Normal fact",
    )
    important_factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.IMPORTANT,
        content="Important fact",
    )
    critical_factoid = FactoidEntity(
        id=uuid4(),
        user_id=test_user.id,
        conversation_id=conversation.id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        criticality=value_objects.FactoidCriticality.CRITICAL,
        content="Critical fact",
    )

    assert not normal_factoid.is_important_or_critical()
    assert important_factoid.is_important_or_critical()
    assert critical_factoid.is_important_or_critical()
