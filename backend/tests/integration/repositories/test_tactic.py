"""Integration tests for TacticRepository."""

from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import TacticEntity
from lykke.infrastructure.repositories import TacticRepository


@pytest.mark.asyncio
async def test_get(tactic_repo, test_user):
    """Test getting a tactic by ID."""
    tactic = TacticEntity(
        user_id=test_user.id,
        name="Guided meditation",
        description="Short calming meditation",
    )
    await tactic_repo.put(tactic)

    result = await tactic_repo.get(tactic.id)

    assert result.id == tactic.id
    assert result.name == "Guided meditation"


@pytest.mark.asyncio
async def test_get_not_found(tactic_repo):
    """Test getting a non-existent tactic raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await tactic_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(tactic_repo, test_user):
    """Test creating a new tactic."""
    tactic = TacticEntity(
        user_id=test_user.id,
        name="Quick journal entry",
        description="Write a few sentences",
    )

    result = await tactic_repo.put(tactic)

    assert result.name == "Quick journal entry"
    assert result.description == "Write a few sentences"


@pytest.mark.asyncio
async def test_all(tactic_repo, test_user):
    """Test getting all tactics."""
    tactic1 = TacticEntity(
        user_id=test_user.id,
        name="Walk outside",
        description="Short walk to reset",
    )
    tactic2 = TacticEntity(
        user_id=test_user.id,
        name="Box breathing",
        description="Inhale 4, hold 4, exhale 4, hold 4",
    )
    await tactic_repo.put(tactic1)
    await tactic_repo.put(tactic2)

    all_tactics = await tactic_repo.all()

    ids = [t.id for t in all_tactics]
    assert tactic1.id in ids
    assert tactic2.id in ids


@pytest.mark.asyncio
async def test_user_isolation(tactic_repo, test_user, create_test_user):
    """Test that different users' tactics are properly isolated."""
    tactic = TacticEntity(
        user_id=test_user.id,
        name="Box breathing",
        description="Inhale 4, hold 4, exhale 4, hold 4",
    )
    await tactic_repo.put(tactic)

    user2 = await create_test_user()
    tactic_repo2 = TacticRepository(user=user2)

    with pytest.raises(NotFoundError):
        await tactic_repo2.get(tactic.id)
