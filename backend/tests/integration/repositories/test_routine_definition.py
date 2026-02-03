"""Integration tests for RoutineDefinitionRepository."""

from datetime import time
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects.routine_definition import (
    RecurrenceSchedule,
    RoutineDefinitionTask,
    TimeWindow,
)
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
from lykke.infrastructure.repositories import RoutineDefinitionRepository


@pytest.mark.asyncio
async def test_get(routine_definition_repo, test_user):
    """Test getting a routine by ID."""
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Routine Definition",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_definition_repo.put(routine_definition)

    result = await routine_definition_repo.get(routine_definition.id)

    assert result.id == routine_definition.id
    assert result.name == "Test Routine Definition"


@pytest.mark.asyncio
async def test_get_not_found(routine_definition_repo):
    """Test getting a non-existent routine raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await routine_definition_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(routine_definition_repo, test_user):
    """Test creating a new routine."""
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="New Routine Definition",
        category=TaskCategory.HOUSE,
        description="New description",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )

    result = await routine_definition_repo.put(routine_definition)

    assert result.name == "New Routine Definition"
    assert result.category == TaskCategory.HOUSE


@pytest.mark.asyncio
async def test_all(routine_definition_repo, test_user):
    """Test getting all routines."""
    routine1 = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Routine Definition 1",
        category=TaskCategory.HOUSE,
        description="Description 1",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine2 = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Routine Definition 2",
        category=TaskCategory.HOUSE,
        description="Description 2",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.WEEKLY),
        tasks=[],
    )
    await routine_definition_repo.put(routine1)
    await routine_definition_repo.put(routine2)

    all_routine_definitions = await routine_definition_repo.all()

    routine_definition_ids = [r.id for r in all_routine_definitions]
    assert routine1.id in routine_definition_ids
    assert routine2.id in routine_definition_ids


@pytest.mark.asyncio
async def test_user_isolation(routine_definition_repo, test_user, create_test_user):
    """Test that different users' routines are properly isolated."""
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="User1 Routine Definition",
        category=TaskCategory.HOUSE,
        description="Description",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_definition_repo.put(routine_definition)

    # Create another user
    user2 = await create_test_user()
    routine_repo2 = RoutineDefinitionRepository(user=user2)

    # User2 should not see user1's routine
    with pytest.raises(NotFoundError):
        await routine_repo2.get(routine_definition.id)


@pytest.mark.asyncio
async def test_put_with_task_time_window(routine_definition_repo, test_user):
    """Ensure tasks with time windows are serialized/deserialized."""
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="With Task Schedule",
        category=TaskCategory.HOUSE,
        description="Has scheduled task",
        routine_definition_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[
            RoutineDefinitionTask(
                task_definition_id=uuid4(),
                name="Test Task",
                time_window=TimeWindow(
                    start_time=time(hour=9, minute=0),
                    end_time=time(hour=10, minute=0),
                ),
            )
        ],
    )

    await routine_definition_repo.put(routine_definition)
    result = await routine_definition_repo.get(routine_definition.id)

    assert result.tasks
    first = result.tasks[0]
    assert first.time_window is not None
    assert first.time_window.start_time == time(hour=9, minute=0)
    assert first.time_window.end_time == time(hour=10, minute=0)
