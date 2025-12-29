"""Integration tests for TaskRepository."""

import datetime
from uuid import uuid4

import pytest
import pytest_asyncio

from planned.core.exceptions import exceptions
from planned.domain.entities import Task
from planned.domain.value_objects.task import (
    TaskCategory,
    TaskDefinition,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskType,
    TimingType,
)
from planned.infrastructure.repositories import TaskRepository
from planned.infrastructure.repositories.base.schema import DateQuery


def _create_task_definition(user_uuid, task_id="test-task"):
    """Helper to create a task definition."""
    return TaskDefinition(
        user_uuid=user_uuid,
        id=task_id,
        name="Test Task",
        description="Test description",
        type=TaskType.ACTIVITY,
    )


@pytest.mark.asyncio
async def test_get(task_repo, test_user, test_date):
    """Test getting a task by ID."""
    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Test Task",
        status=TaskStatus.READY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
    )
    await task_repo.put(task)

    result = await task_repo.get(task.id)

    assert result.id == task.id
    assert result.name == "Test Task"
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_get_not_found(task_repo):
    """Test getting a non-existent task raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await task_repo.get(str(uuid4()))


@pytest.mark.asyncio
async def test_put(task_repo, test_user, test_date):
    """Test creating a new task."""
    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="New Task",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
    )

    result = await task_repo.put(task)

    assert result.name == "New Task"
    assert result.user_uuid == test_user.uuid
    assert result.scheduled_date == test_date


@pytest.mark.asyncio
async def test_put_update(task_repo, test_user, test_date):
    """Test updating an existing task."""
    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Original Task",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
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
    task1 = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Task 1",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid, "task1"),
    )
    task2 = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Task 2",
        status=TaskStatus.READY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date_tomorrow,
        task_definition=_create_task_definition(test_user.uuid, "task2"),
    )
    await task_repo.put(task1)
    await task_repo.put(task2)

    all_tasks = await task_repo.all()

    task_ids = [t.id for t in all_tasks]
    assert task1.id in task_ids
    assert task2.id in task_ids


@pytest.mark.asyncio
async def test_search_query(task_repo, test_user, test_date, test_date_tomorrow):
    """Test searching tasks with DateQuery."""
    task1 = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Task Today",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid, "task1"),
    )
    task2 = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Task Tomorrow",
        status=TaskStatus.READY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date_tomorrow,
        task_definition=_create_task_definition(test_user.uuid, "task2"),
    )
    await task_repo.put(task1)
    await task_repo.put(task2)

    # Search for specific date
    results = await task_repo.search_query(DateQuery(date=test_date))

    assert len(results) == 1
    assert results[0].scheduled_date == test_date
    assert results[0].name == "Task Today"


@pytest.mark.asyncio
async def test_delete(task_repo, test_user, test_date):
    """Test deleting a task."""
    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Task to Delete",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
    )
    await task_repo.put(task)

    # Delete it
    await task_repo.delete(task)

    # Should not be found
    with pytest.raises(exceptions.NotFoundError):
        await task_repo.get(task.id)


@pytest.mark.asyncio
async def test_user_isolation(task_repo, test_user, create_test_user, test_date):
    """Test that different users' tasks are properly isolated."""
    # Create task for test_user
    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="User1 Task",
        status=TaskStatus.NOT_STARTED,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
    )
    await task_repo.put(task)

    # Create another user
    user2 = await create_test_user()
    task_repo2 = TaskRepository(user_uuid=user2.uuid)

    # User2 should not see user1's task
    with pytest.raises(exceptions.NotFoundError):
        await task_repo2.get(task.id)

    # User1 should still see their task
    result = await task_repo.get(task.id)
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_task_with_schedule(task_repo, test_user, test_date):
    """Test creating a task with a schedule."""
    schedule = TaskSchedule(
        timing_type=TimingType.DEADLINE,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
    )

    task = Task(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        name="Scheduled Task",
        status=TaskStatus.READY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
        task_definition=_create_task_definition(test_user.uuid),
        schedule=schedule,
    )

    result = await task_repo.put(task)

    assert result.schedule is not None
    assert result.schedule.start_time == datetime.time(10, 0)
    assert result.schedule.end_time == datetime.time(12, 0)

