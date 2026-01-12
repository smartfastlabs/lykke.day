"""Integration tests for BotPersonalityRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import BotPersonalityEntity


@pytest.mark.asyncio
async def test_get(bot_personality_repo, test_user):
    """Test getting a bot personality by ID."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Tough Love Coach",
        system_prompt="You are a tough love coach who helps people achieve their goals.",
    )
    await bot_personality_repo.put(personality)

    result = await bot_personality_repo.get(personality.id)

    assert result.id == personality.id
    assert result.user_id == test_user.id
    assert result.name == "Tough Love Coach"
    assert result.system_prompt == personality.system_prompt


@pytest.mark.asyncio
async def test_get_not_found(bot_personality_repo):
    """Test getting a non-existent bot personality raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await bot_personality_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(bot_personality_repo, test_user):
    """Test creating a new bot personality."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Gentle Supporter",
        system_prompt="You are a gentle, supportive assistant.",
        user_amendments="Always ask about sleep quality.",
        meta={"category": "wellness", "version": 1},
    )

    result = await bot_personality_repo.put(personality)

    assert result.id == personality.id
    assert result.name == "Gentle Supporter"
    assert result.user_amendments == "Always ask about sleep quality."
    assert result.meta == {"category": "wellness", "version": 1}


@pytest.mark.asyncio
async def test_put_update(bot_personality_repo, test_user):
    """Test updating an existing bot personality."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Original Name",
        system_prompt="Original prompt",
    )
    await bot_personality_repo.put(personality)

    # Update via apply_update
    update = value_objects.BotPersonalityUpdateObject(
        name="Updated Name", user_amendments="New amendments"
    )
    updated = personality.apply_update(update)
    result = await bot_personality_repo.put(updated)

    assert result.name == "Updated Name"
    assert result.user_amendments == "New amendments"

    # Verify it was saved
    retrieved = await bot_personality_repo.get(personality.id)
    assert retrieved.name == "Updated Name"


@pytest.mark.asyncio
async def test_system_personality(bot_personality_repo):
    """Test creating a system-wide personality (no user_id)."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=None,
        name="Default Assistant",
        system_prompt="You are a helpful AI assistant.",
    )
    await bot_personality_repo.put(personality)

    result = await bot_personality_repo.get(personality.id)
    assert result.user_id is None
    assert result.is_system_default()


@pytest.mark.asyncio
async def test_search_by_name(bot_personality_repo, test_user):
    """Test searching bot personalities by name."""
    personality1 = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Coach",
        system_prompt="Coaching prompt",
    )
    personality2 = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Therapist",
        system_prompt="Therapy prompt",
    )
    await bot_personality_repo.put(personality1)
    await bot_personality_repo.put(personality2)

    results = await bot_personality_repo.search(
        value_objects.BotPersonalityQuery(name="Coach")
    )

    assert len(results) == 1
    assert results[0].id == personality1.id


@pytest.mark.asyncio
async def test_search_includes_system_personalities(bot_personality_repo, test_user):
    """Test that user-scoped search includes both user and system personalities."""
    user_personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="User Personality",
        system_prompt="User prompt",
    )
    system_personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=None,
        name="System Personality",
        system_prompt="System prompt",
    )
    await bot_personality_repo.put(user_personality)
    await bot_personality_repo.put(system_personality)

    # When searching with user-scoped repo, should get both
    results = await bot_personality_repo.all()

    personality_ids = [p.id for p in results]
    assert user_personality.id in personality_ids
    assert system_personality.id in personality_ids


@pytest.mark.asyncio
async def test_personality_inheritance(bot_personality_repo, test_user):
    """Test bot personality with base personality inheritance."""
    base_personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=None,
        name="Base Personality",
        system_prompt="Base system prompt",
    )
    await bot_personality_repo.put(base_personality)

    derived_personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Derived Personality",
        base_bot_personality_id=base_personality.id,
        system_prompt="Base system prompt",
        user_amendments="Additional user-specific instructions",
    )
    await bot_personality_repo.put(derived_personality)

    result = await bot_personality_repo.get(derived_personality.id)
    assert result.base_bot_personality_id == base_personality.id
    assert result.get_full_prompt().startswith("Base system prompt")
    assert "Additional user-specific instructions" in result.get_full_prompt()


@pytest.mark.asyncio
async def test_search_by_base_personality(bot_personality_repo, test_user):
    """Test searching personalities by base_bot_personality_id."""
    base_id = uuid4()
    personality1 = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Derived 1",
        base_bot_personality_id=base_id,
        system_prompt="Prompt 1",
    )
    personality2 = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Derived 2",
        base_bot_personality_id=base_id,
        system_prompt="Prompt 2",
    )
    personality3 = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Independent",
        system_prompt="Independent prompt",
    )
    await bot_personality_repo.put(personality1)
    await bot_personality_repo.put(personality2)
    await bot_personality_repo.put(personality3)

    results = await bot_personality_repo.search(
        value_objects.BotPersonalityQuery(base_bot_personality_id=base_id)
    )

    assert len(results) == 2
    result_ids = [p.id for p in results]
    assert personality1.id in result_ids
    assert personality2.id in result_ids


@pytest.mark.asyncio
async def test_entity_to_row_and_back(bot_personality_repo, test_user):
    """Test round-trip conversion: entity -> row -> entity."""
    original = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Personality",
        base_bot_personality_id=uuid4(),
        system_prompt="You are a test personality for integration testing.",
        user_amendments="Be extra thorough with explanations.",
        meta={"version": 2, "tags": ["test", "experimental"]},
        created_at=datetime(2025, 1, 20, 9, 0, 0, tzinfo=UTC),
    )

    # Convert to row
    row = bot_personality_repo.entity_to_row(original)

    # Verify row structure
    assert row["id"] == original.id
    assert row["user_id"] == test_user.id
    assert row["name"] == "Test Personality"
    assert row["base_bot_personality_id"] == original.base_bot_personality_id
    assert row["system_prompt"] == original.system_prompt
    assert row["user_amendments"] == "Be extra thorough with explanations."
    assert row["meta"] == {"version": 2, "tags": ["test", "experimental"]}

    # Convert back to entity
    restored = bot_personality_repo.row_to_entity(row)

    # Verify entity matches original
    assert restored.id == original.id
    assert restored.user_id == original.user_id
    assert restored.name == original.name
    assert restored.base_bot_personality_id == original.base_bot_personality_id
    assert restored.system_prompt == original.system_prompt
    assert restored.user_amendments == original.user_amendments
    assert restored.meta == original.meta
    assert restored.created_at == original.created_at


@pytest.mark.asyncio
async def test_empty_fields_handling(bot_personality_repo, test_user):
    """Test that empty user_amendments and meta are properly handled."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Minimal Personality",
        system_prompt="Basic prompt",
        user_amendments="",
        meta={},
    )
    await bot_personality_repo.put(personality)

    retrieved = await bot_personality_repo.get(personality.id)
    assert retrieved.user_amendments == ""
    assert retrieved.meta == {}
