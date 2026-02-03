"""Integration tests for TimeBlockDefinitionRepository."""

from typing import Any
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity
from lykke.infrastructure.repositories import TimeBlockDefinitionRepository


@pytest.mark.asyncio
async def test_get(time_block_definition_repo: Any, test_user: Any) -> None:
    """Test getting a time block definition by ID."""
    time_block_def = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Morning Work Block",
        description="Focused work time in the morning",
        type=value_objects.TimeBlockType.WORK,
        category=value_objects.TimeBlockCategory.WORK,
    )
    await time_block_definition_repo.put(time_block_def)

    result = await time_block_definition_repo.get(time_block_def.id)

    assert result.id == time_block_def.id
    assert result.name == "Morning Work Block"
    assert result.type == value_objects.TimeBlockType.WORK
    assert result.category == value_objects.TimeBlockCategory.WORK


@pytest.mark.asyncio
async def test_get_not_found(time_block_definition_repo: Any) -> None:
    """Test getting a non-existent time block definition raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await time_block_definition_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put_creates_new(time_block_definition_repo: Any, test_user: Any) -> None:
    """Test creating a new time block definition."""
    time_block_def = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Lunch Break",
        description="Midday meal",
        type=value_objects.TimeBlockType.MEAL,
        category=value_objects.TimeBlockCategory.NUTRITION,
    )

    result = await time_block_definition_repo.put(time_block_def)

    assert result.name == "Lunch Break"
    assert result.type == value_objects.TimeBlockType.MEAL
    assert result.category == value_objects.TimeBlockCategory.NUTRITION


@pytest.mark.asyncio
async def test_put_updates_existing(
    time_block_definition_repo: Any, test_user: Any
) -> None:
    """Test updating an existing time block definition."""
    time_block_def = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Exercise",
        description="Morning workout",
        type=value_objects.TimeBlockType.EXERCISE,
        category=value_objects.TimeBlockCategory.FITNESS,
    )
    await time_block_definition_repo.put(time_block_def)

    # Update the definition
    time_block_def.name = "Evening Exercise"
    time_block_def.description = "Evening workout session"
    result = await time_block_definition_repo.put(time_block_def)

    assert result.id == time_block_def.id
    assert result.name == "Evening Exercise"
    assert result.description == "Evening workout session"

    # Verify it was updated in the database
    retrieved = await time_block_definition_repo.get(time_block_def.id)
    assert retrieved.name == "Evening Exercise"


@pytest.mark.asyncio
async def test_enum_conversion(time_block_definition_repo: Any, test_user: Any) -> None:
    """Test that enums are properly converted to/from database."""
    # Test all enum types
    test_cases = [
        (
            value_objects.TimeBlockType.WORK,
            value_objects.TimeBlockCategory.PROFESSIONAL,
        ),
        (value_objects.TimeBlockType.BREAK, value_objects.TimeBlockCategory.RECREATION),
        (value_objects.TimeBlockType.MEAL, value_objects.TimeBlockCategory.NUTRITION),
        (value_objects.TimeBlockType.EXERCISE, value_objects.TimeBlockCategory.FITNESS),
        (value_objects.TimeBlockType.COMMUTE, value_objects.TimeBlockCategory.COMMUTE),
    ]

    for block_type, category in test_cases:
        time_block_def = TimeBlockDefinitionEntity(
            user_id=test_user.id,
            name=f"Test {block_type.value}",
            description=f"Test {category.value}",
            type=block_type,
            category=category,
        )
        await time_block_definition_repo.put(time_block_def)

        # Retrieve and verify enums are correct
        result = await time_block_definition_repo.get(time_block_def.id)
        assert result.type == block_type
        assert result.category == category
        assert isinstance(result.type, value_objects.TimeBlockType)
        assert isinstance(result.category, value_objects.TimeBlockCategory)


@pytest.mark.asyncio
async def test_all(time_block_definition_repo: Any, test_user: Any) -> None:
    """Test getting all time block definitions."""
    time_block_def1 = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Morning Work",
        description="Morning work session",
        type=value_objects.TimeBlockType.WORK,
        category=value_objects.TimeBlockCategory.WORK,
    )
    time_block_def2 = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Lunch",
        description="Lunch break",
        type=value_objects.TimeBlockType.MEAL,
        category=value_objects.TimeBlockCategory.NUTRITION,
    )
    await time_block_definition_repo.put(time_block_def1)
    await time_block_definition_repo.put(time_block_def2)

    all_defs = await time_block_definition_repo.all()

    def_ids = [d.id for d in all_defs]
    assert time_block_def1.id in def_ids
    assert time_block_def2.id in def_ids

    # Verify enums are properly deserialized
    for def_ in all_defs:
        assert isinstance(def_.type, value_objects.TimeBlockType)
        assert isinstance(def_.category, value_objects.TimeBlockCategory)


@pytest.mark.asyncio
async def test_user_isolation(
    time_block_definition_repo: Any, test_user: Any, create_test_user: Any
) -> None:
    """Test that different users' time block definitions are properly isolated."""
    time_block_def = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="User1 Work Block",
        description="User1's work time",
        type=value_objects.TimeBlockType.WORK,
        category=value_objects.TimeBlockCategory.WORK,
    )
    await time_block_definition_repo.put(time_block_def)

    # Create another user
    user2 = await create_test_user()
    time_block_definition_repo2 = TimeBlockDefinitionRepository(user=user2)

    # User2 should not see user1's time block definition
    with pytest.raises(NotFoundError):
        await time_block_definition_repo2.get(time_block_def.id)

    # User2's all() should not include user1's definitions
    user2_defs = await time_block_definition_repo2.all()
    user2_def_ids = [d.id for d in user2_defs]
    assert time_block_def.id not in user2_def_ids


@pytest.mark.asyncio
async def test_delete(time_block_definition_repo: Any, test_user: Any) -> None:
    """Test deleting a time block definition."""
    time_block_def = TimeBlockDefinitionEntity(
        user_id=test_user.id,
        name="Temporary Block",
        description="This will be deleted",
        type=value_objects.TimeBlockType.BREAK,
        category=value_objects.TimeBlockCategory.RECREATION,
    )
    await time_block_definition_repo.put(time_block_def)

    # Verify it exists
    result = await time_block_definition_repo.get(time_block_def.id)
    assert result.id == time_block_def.id

    # Delete it
    await time_block_definition_repo.delete(time_block_def.id)

    # Verify it's gone
    with pytest.raises(NotFoundError):
        await time_block_definition_repo.get(time_block_def.id)
