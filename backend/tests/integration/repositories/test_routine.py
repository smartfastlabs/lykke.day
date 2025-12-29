"""Integration tests for RoutineRepository."""

from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from planned.core.exceptions import exceptions
from planned.domain.entities import Routine
from planned.infrastructure.repositories import RoutineRepository
from planned.domain.value_objects.routine import RoutineSchedule
from planned.domain.value_objects.task import TaskCategory, TaskFrequency


@pytest.mark.asyncio
async def test_get(routine_repo, test_user):
    """Test getting a routine by ID."""
    routine = Routine(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_repo.put(routine)
    
    result = await routine_repo.get(routine.id)
    
    assert result.id == routine.id
    assert result.name == "Test Routine"


@pytest.mark.asyncio
async def test_get_not_found(routine_repo):
    """Test getting a non-existent routine raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await routine_repo.get(str(uuid4()))


@pytest.mark.asyncio
async def test_put(routine_repo, test_user):
    """Test creating a new routine."""
    routine = Routine(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="New Routine",
        category=TaskCategory.HOUSE,
        description="New description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    
    result = await routine_repo.put(routine)
    
    assert result.name == "New Routine"
    assert result.category == TaskCategory.HOUSE


@pytest.mark.asyncio
async def test_all(routine_repo, test_user):
    """Test getting all routines."""
    routine1 = Routine(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Routine 1",
        category=TaskCategory.HOUSE,
        description="Description 1",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine2 = Routine(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Routine 2",
        category=TaskCategory.HOUSE,
        description="Description 2",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.WEEKLY),
        tasks=[],
    )
    await routine_repo.put(routine1)
    await routine_repo.put(routine2)
    
    all_routines = await routine_repo.all()
    
    routine_ids = [r.id for r in all_routines]
    assert routine1.id in routine_ids
    assert routine2.id in routine_ids


@pytest.mark.asyncio
async def test_user_isolation(routine_repo, test_user, create_test_user):
    """Test that different users' routines are properly isolated."""
    routine = Routine(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="User1 Routine",
        category=TaskCategory.HOUSE,
        description="Description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_repo.put(routine)
    
    # Create another user
    user2 = await create_test_user()
    routine_repo2 = RoutineRepository(user_uuid=user2.uuid)
    
    # User2 should not see user1's routine
    with pytest.raises(exceptions.NotFoundError):
        await routine_repo2.get(routine.id)

