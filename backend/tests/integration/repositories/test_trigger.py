"""Integration tests for TriggerRepository."""

from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import TacticEntity, TriggerEntity
from lykke.infrastructure.repositories import TriggerRepository


@pytest.mark.asyncio
async def test_get(trigger_repo, test_user):
    """Test getting a trigger by ID."""
    trigger = TriggerEntity(
        user_id=test_user.id,
        name="Anxiety Attack",
        description="Sudden anxiety spike",
    )
    await trigger_repo.put(trigger)

    result = await trigger_repo.get(trigger.id)

    assert result.id == trigger.id
    assert result.name == "Anxiety Attack"


@pytest.mark.asyncio
async def test_get_not_found(trigger_repo):
    """Test getting a non-existent trigger raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await trigger_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(trigger_repo, test_user):
    """Test creating a new trigger."""
    trigger = TriggerEntity(
        user_id=test_user.id,
        name="Late",
        description="Running behind schedule",
    )

    result = await trigger_repo.put(trigger)

    assert result.name == "Late"
    assert result.description == "Running behind schedule"


@pytest.mark.asyncio
async def test_all(trigger_repo, test_user):
    """Test getting all triggers."""
    trigger1 = TriggerEntity(
        user_id=test_user.id,
        name="Work Stress",
        description="Overwhelmed by work",
    )
    trigger2 = TriggerEntity(
        user_id=test_user.id,
        name="Can't Sleep",
        description="Trouble falling asleep",
    )
    await trigger_repo.put(trigger1)
    await trigger_repo.put(trigger2)

    all_triggers = await trigger_repo.all()

    ids = [t.id for t in all_triggers]
    assert trigger1.id in ids
    assert trigger2.id in ids


@pytest.mark.asyncio
async def test_user_isolation(trigger_repo, test_user, create_test_user):
    """Test that different users' triggers are properly isolated."""
    trigger = TriggerEntity(
        user_id=test_user.id,
        name="Want to Drink",
        description="Craving alcohol",
    )
    await trigger_repo.put(trigger)

    user2 = await create_test_user()
    trigger_repo2 = TriggerRepository(user_id=user2.id)

    with pytest.raises(NotFoundError):
        await trigger_repo2.get(trigger.id)


@pytest.mark.asyncio
async def test_set_and_list_tactics(trigger_repo, tactic_repo, test_user):
    """Test linking tactics to a trigger."""
    trigger = TriggerEntity(
        user_id=test_user.id,
        name="Anxiety Attack",
        description="Sudden anxiety spike",
    )
    await trigger_repo.put(trigger)

    tactic1 = TacticEntity(
        user_id=test_user.id,
        name="Box breathing",
        description="Inhale 4, hold 4, exhale 4, hold 4",
    )
    tactic2 = TacticEntity(
        user_id=test_user.id,
        name="Guided meditation",
        description="Short calming meditation",
    )
    await tactic_repo.put(tactic1)
    await tactic_repo.put(tactic2)

    await trigger_repo.set_tactics_for_trigger(trigger.id, [tactic1.id, tactic2.id])
    tactics = await trigger_repo.list_tactics_for_trigger(trigger.id)
    tactic_ids = {t.id for t in tactics}

    assert tactic1.id in tactic_ids
    assert tactic2.id in tactic_ids
