"""Integration tests for TaskRepository."""

import datetime
from uuid import uuid4, uuid5

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import TaskEntity
from lykke.domain.value_objects.query import TaskQuery
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskType,
    TimingType,
)
from lykke.infrastructure.repositories import TaskRepository


@pytest.mark.asyncio
async def test_get(task_repo, test_user, test_date):
    """Test getting a task by ID."""
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Task",
        status=TaskStatus.READY,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(task)

    result = await task_repo.get(task.id)

    assert result.id == task.id
    assert result.name == "Test Task"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_not_found(task_repo):
    """Test getting a non-existent task raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await task_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(task_repo, test_user, test_date):
    """Test creating a new task."""
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="New Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )

    result = await task_repo.put(task)

    assert result.name == "New Task"
    assert result.user_id == test_user.id
    assert result.scheduled_date == test_date


@pytest.mark.asyncio
async def test_put_update(task_repo, test_user, test_date):
    """Test updating an existing task."""
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Original Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(task)

    # Update the task
    task.name = "Updated Task"
    task.status = TaskStatus.COMPLETE
    result = await task_repo.put(task)

    assert result.name == "Updated Task"
    assert result.status == TaskStatus.COMPLETE

    # Verify it was saved
    retrieved = await task_repo.get(task.id)
    assert retrieved.name == "Updated Task"
    assert retrieved.status == TaskStatus.COMPLETE


@pytest.mark.asyncio
async def test_all(task_repo, test_user, test_date, test_date_tomorrow):
    """Test getting all tasks."""
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Task 1",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Task 2",
        status=TaskStatus.READY,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date_tomorrow,
    )
    await task_repo.put(task1)
    await task_repo.put(task2)

    all_tasks = await task_repo.all()

    task_ids = [t.id for t in all_tasks]
    assert task1.id in task_ids
    assert task2.id in task_ids


@pytest.mark.asyncio
async def test_search_query(task_repo, test_user, test_date, test_date_tomorrow):
    """Test searching tasks with TaskQuery."""
    task1 = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Task Today",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    task2 = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Task Tomorrow",
        status=TaskStatus.READY,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date_tomorrow,
    )
    await task_repo.put(task1)
    await task_repo.put(task2)

    # Search for specific date
    results = await task_repo.search(TaskQuery(date=test_date))

    assert len(results) == 1
    assert results[0].scheduled_date == test_date
    assert results[0].name == "Task Today"


@pytest.mark.asyncio
async def test_delete(task_repo, test_user, test_date):
    """Test deleting a task."""
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Task to Delete",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(task)

    # Delete it
    await task_repo.delete(task)

    # Should not be found
    with pytest.raises(NotFoundError):
        await task_repo.get(task.id)


@pytest.mark.asyncio
async def test_user_isolation(task_repo, test_user, create_test_user, test_date):
    """Test that different users' tasks are properly isolated."""
    # Create task for test_user
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="User1 Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(task)

    # Create another user
    user2 = await create_test_user()
    task_repo2 = TaskRepository(user_id=user2.id)

    # User2 should not see user1's task
    with pytest.raises(NotFoundError):
        await task_repo2.get(task.id)

    # User1 should still see their task
    result = await task_repo.get(task.id)
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_task_with_schedule(task_repo, test_user, test_date):
    """Test creating a task with a schedule."""
    schedule = TaskSchedule(
        timing_type=TimingType.DEADLINE,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
    )

    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Scheduled Task",
        status=TaskStatus.READY,
        type=TaskType.ACTIVITY,
        description="Test description",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        schedule=schedule,
    )

    result = await task_repo.put(task)

    assert result.schedule is not None
    assert result.schedule.start_time == datetime.time(10, 0)
    assert result.schedule.end_time == datetime.time(12, 0)


def test_row_to_entity_parses_time_strings(test_user, test_date):
    """Ensure time-only strings in schedule JSON deserialize without ValueError."""
    schedule_dict = {
        "timing_type": TimingType.DEADLINE.value,
        "start_time": "20:00:00",
        "end_time": None,
        "available_time": None,
    }
    row = {
        "id": uuid4(),
        "user_id": test_user.id,
        "date": test_date,
        "scheduled_date": test_date,
        "name": "String schedule task",
        "status": TaskStatus.READY.value,
        "type": TaskType.ACTIVITY.value,
        "description": "Test description",
        "category": TaskCategory.HOUSE.value,
        "frequency": TaskFrequency.DAILY.value,
        "completed_at": None,
        "schedule": schedule_dict,
        "routine_id": None,
        "tags": [],
        "actions": [],
    }

    entity = TaskRepository.row_to_entity(row)

    assert entity.schedule is not None
    assert entity.schedule.start_time == datetime.time(20, 0)


def test_entity_to_row_and_back_preserves_enums(test_user, test_date):
    """Test that converting a task entity to row and back preserves enum values correctly.

    This is a regression test for a bug where str(task.status) was producing
    'TaskStatus.NOT_STARTED' instead of 'NOT_STARTED', causing deserialization to fail.
    """
    # Create a task entity with various enum values
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Enum Test Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.CHORE,
        description="Testing enum serialization",
        category=TaskCategory.CLEANING,
        frequency=TaskFrequency.WEEKLY,
        scheduled_date=test_date,
    )

    # Convert to row (simulating save to database)
    row = TaskRepository.entity_to_row(task)

    # Verify the row has string values, not enum representations
    assert row["status"] == "NOT_STARTED", (
        f"Expected 'NOT_STARTED', got {row['status']}"
    )
    assert row["type"] == "CHORE", f"Expected 'CHORE', got {row['type']}"
    assert row["category"] == "CLEANING", f"Expected 'CLEANING', got {row['category']}"
    assert row["frequency"] == "WEEKLY", f"Expected 'WEEKLY', got {row['frequency']}"

    # Convert back to entity (simulating load from database)
    restored_task = TaskRepository.row_to_entity(row)

    # Verify enums are properly restored
    assert restored_task.status == TaskStatus.NOT_STARTED
    assert restored_task.type == TaskType.CHORE
    assert restored_task.category == TaskCategory.CLEANING
    assert restored_task.frequency == TaskFrequency.WEEKLY
    assert restored_task.name == task.name
    assert restored_task.id == task.id
