"""Unit tests for BotPersonalityEntity domain logic."""

from uuid import uuid4

import pytest

from lykke.domain.entities import BotPersonalityEntity


@pytest.fixture
def bot_personality() -> BotPersonalityEntity:
    """Create a test bot personality entity."""
    return BotPersonalityEntity(
        id=uuid4(),
        user_id=uuid4(),
        name="Friendly Assistant",
        system_prompt="You are a friendly and helpful assistant.",
    )


def test_bot_personality_creation() -> None:
    """Test creating a bot personality entity."""
    user_id = uuid4()
    name = "Professional Coach"
    system_prompt = "You are a professional life coach."

    personality = BotPersonalityEntity(
        user_id=user_id,
        name=name,
        system_prompt=system_prompt,
    )

    assert personality.user_id == user_id
    assert personality.name == name
    assert personality.system_prompt == system_prompt
    assert personality.user_amendments == ""
    assert personality.base_bot_personality_id is None
    assert personality.meta == {}
    assert personality.created_at is not None


def test_system_default_personality() -> None:
    """Test creating a system default personality (no user_id)."""
    personality = BotPersonalityEntity(
        user_id=None,
        name="Default Assistant",
        system_prompt="Default system prompt",
    )

    assert personality.user_id is None
    assert personality.is_system_default() is True


def test_user_specific_personality(bot_personality: BotPersonalityEntity) -> None:
    """Test user-specific personality is not a system default."""
    assert bot_personality.user_id is not None
    assert bot_personality.is_system_default() is False


def test_get_full_prompt_without_amendments(
    bot_personality: BotPersonalityEntity,
) -> None:
    """Test getting full prompt when no amendments exist."""
    full_prompt = bot_personality.get_full_prompt()
    assert full_prompt == bot_personality.system_prompt
    assert "\n\n" not in full_prompt


def test_get_full_prompt_with_amendments() -> None:
    """Test getting full prompt with user amendments."""
    system_prompt = "You are a helpful assistant."
    amendments = "Always be extra polite and use emojis."

    personality = BotPersonalityEntity(
        user_id=uuid4(),
        name="Custom Assistant",
        system_prompt=system_prompt,
        user_amendments=amendments,
    )

    full_prompt = personality.get_full_prompt()
    assert full_prompt == f"{system_prompt}\n\n{amendments}"
    assert system_prompt in full_prompt
    assert amendments in full_prompt


def test_get_full_prompt_with_empty_amendments() -> None:
    """Test that empty string amendments don't add extra spacing."""
    personality = BotPersonalityEntity(
        user_id=uuid4(),
        name="Test",
        system_prompt="Base prompt",
        user_amendments="",
    )

    full_prompt = personality.get_full_prompt()
    assert full_prompt == "Base prompt"


def test_personality_inheritance() -> None:
    """Test personality that inherits from a base personality."""
    base_id = uuid4()
    user_id = uuid4()

    derived_personality = BotPersonalityEntity(
        user_id=user_id,
        name="My Custom Assistant",
        base_bot_personality_id=base_id,
        system_prompt="Base personality prompt",
        user_amendments="My customizations",
    )

    assert derived_personality.base_bot_personality_id == base_id
    assert derived_personality.user_id == user_id


def test_personality_with_metadata() -> None:
    """Test personality with custom metadata."""
    meta_data = {
        "tone": "professional",
        "verbosity": "concise",
        "use_emojis": False,
    }

    personality = BotPersonalityEntity(
        user_id=uuid4(),
        name="Professional",
        system_prompt="Be professional",
        meta=meta_data,
    )

    assert personality.meta == meta_data


def test_personality_immutability() -> None:
    """Test that personality entities are immutable (via clone)."""
    original = BotPersonalityEntity(
        user_id=uuid4(),
        name="Original",
        system_prompt="Original prompt",
    )

    # Clone with updated name
    updated = original.clone(name="Updated")

    assert original.name == "Original"
    assert updated.name == "Updated"
    assert original.id == updated.id  # ID preserved
    assert original is not updated  # Different instances


def test_system_vs_user_personalities() -> None:
    """Test distinction between system and user personalities."""
    # System personality
    system_personality = BotPersonalityEntity(
        user_id=None,
        name="System Default",
        system_prompt="System prompt",
    )
    assert system_personality.is_system_default() is True

    # User personality
    user_personality = BotPersonalityEntity(
        user_id=uuid4(),
        name="User Custom",
        system_prompt="User prompt",
    )
    assert user_personality.is_system_default() is False


def test_complex_amendments() -> None:
    """Test personality with complex multi-line amendments."""
    system_prompt = "You are a coding assistant."
    amendments = """Additional instructions:
- Always explain your reasoning
- Provide examples when possible
- Ask clarifying questions if needed"""

    personality = BotPersonalityEntity(
        user_id=uuid4(),
        name="Code Helper",
        system_prompt=system_prompt,
        user_amendments=amendments,
    )

    full_prompt = personality.get_full_prompt()
    assert system_prompt in full_prompt
    assert "Additional instructions:" in full_prompt
    assert "Always explain your reasoning" in full_prompt
