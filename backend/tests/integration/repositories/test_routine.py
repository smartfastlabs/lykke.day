"""Integration tests for RoutineRepository."""

from datetime import time
from uuid import uuid4

import pytest
from planned.core.exceptions import NotFoundError
from planned.domain.entities import RoutineEntity
from planned.domain.value_objects.routine import RoutineSchedule, RoutineTask
from planned.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TimingType,
)
from planned.infrastructure.repositories import RoutineRepository


@pytest.mark.asyncio
async def test_get(routine_repo, test_user):
    """Test getting a routine by ID."""
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
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
    with pytest.raises(NotFoundError):
        await routine_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(routine_repo, test_user):
    """Test creating a new routine."""
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
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
    routine1 = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Routine 1",
        category=TaskCategory.HOUSE,
        description="Description 1",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine2 = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
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
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="User1 Routine",
        category=TaskCategory.HOUSE,
        description="Description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_repo.put(routine)

    # Create another user
    user2 = await create_test_user()
    routine_repo2 = RoutineRepository(user_id=user2.id)

    # User2 should not see user1's routine
    with pytest.raises(NotFoundError):
        await routine_repo2.get(routine.id)


@pytest.mark.asyncio
async def test_put_with_task_schedule(routine_repo, test_user):
    """Ensure tasks with schedules are serialized/deserialized."""
    routine = RoutineEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="With Task Schedule",
        category=TaskCategory.HOUSE,
        description="Has scheduled task",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[
            RoutineTask(
                task_definition_id=uuid4(),
                name="Test Task",
                schedule=TaskSchedule(
                    timing_type=TimingType.FIXED_TIME,
                    start_time=time(hour=9, minute=0),
                    end_time=time(hour=10, minute=0),
                ),
            )
        ],
    )

    await routine_repo.put(routine)
    result = await routine_repo.get(routine.id)

    assert result.tasks
    first = result.tasks[0]
    assert first.schedule is not None
    assert first.schedule.start_time == time(hour=9, minute=0)
    assert first.schedule.end_time == time(hour=10, minute=0)
