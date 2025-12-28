"""Tests for transaction management."""

import pytest

from planned.domain.entities import Day, DayStatus, Task, TaskStatus
from planned.infrastructure.database.transaction import TransactionManager, get_transaction_connection
from planned.infrastructure.repositories import DayRepository, TaskRepository
from planned.infrastructure.utils.dates import get_current_datetime


@pytest.fixture
def day_repo():
    return DayRepository()


@pytest.fixture
def task_repo():
    return TaskRepository()


@pytest.mark.asyncio
async def test_transaction_commits_on_success(test_date, day_repo):
    """Test that a transaction commits successfully when no exception occurs."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    async with TransactionManager():
        await day_repo.put(day)

    # After transaction commits, the day should be retrievable
    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_transaction_rolls_back_on_exception(test_date, day_repo):
    """Test that a transaction rolls back when an exception occurs."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    with pytest.raises(ValueError):
        async with TransactionManager():
            await day_repo.put(day)
            raise ValueError("Test exception")

    # After rollback, the day should not be in the database
    from planned.core.exceptions import exceptions

    with pytest.raises(exceptions.NotFoundError):
        await day_repo.get(str(test_date))


@pytest.mark.asyncio
async def test_repository_works_without_transaction(test_date, day_repo):
    """Test that repositories work correctly without an active transaction."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    # No transaction - should create its own connection
    await day_repo.put(day)

    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_read_operations_see_uncommitted_changes(test_date, day_repo):
    """Test that read operations within a transaction see uncommitted changes."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    async with TransactionManager():
        # Put the day in the transaction
        await day_repo.put(day)

        # Read it back - should see the uncommitted change
        result = await day_repo.get(str(test_date))
        assert result.status == DayStatus.SCHEDULED

        # Update it
        day.status = DayStatus.UNSCHEDULED
        await day_repo.put(day)

        # Read it again - should see the updated uncommitted change
        result = await day_repo.get(str(test_date))
        assert result.status == DayStatus.UNSCHEDULED

    # After commit, the final state should be persisted
    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_multiple_operations_in_single_transaction(test_date, day_repo, task_repo):
    """Test that multiple operations in a single transaction are atomic."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    task = Task(
        name="Test Task",
        status=TaskStatus.NOT_STARTED,
        category="HOUSE",
        frequency="DAILY",
        scheduled_date=test_date,
        task_definition={
            "id": "test-task",
            "name": "Test Task",
            "description": "Test",
            "type": "ACTIVITY",
        },
    )

    async with TransactionManager():
        await day_repo.put(day)
        await task_repo.put(task)

    # Both should be committed
    result_day = await day_repo.get(str(test_date))
    assert result_day.status == DayStatus.SCHEDULED

    # Find the task
    from planned.infrastructure.repositories.base import DateQuery

    tasks = await task_repo.search_query(DateQuery(date=test_date))
    assert len(tasks) == 1
    assert tasks[0].name == "Test Task"


@pytest.mark.asyncio
async def test_nested_transactions_reuse_connection(test_date, day_repo):
    """Test that nested transactions reuse the same connection."""
    day1 = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    # Create a nested transaction scenario
    async with TransactionManager() as outer_conn:
        await day_repo.put(day1)

        # Check that we're using the same connection
        active_conn = get_transaction_connection()
        assert active_conn is not None
        assert active_conn is outer_conn

        # Nested transaction should reuse the same connection
        async with TransactionManager() as inner_conn:
            assert inner_conn is outer_conn

            # Update the day
            day1.status = DayStatus.UNSCHEDULED
            await day_repo.put(day1)

    # After commit, the final state should be persisted
    result = await day_repo.get(str(test_date))
    assert result.status == DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_transaction_connection_is_none_outside_transaction():
    """Test that get_transaction_connection returns None when no transaction is active."""
    conn = get_transaction_connection()
    assert conn is None


@pytest.mark.asyncio
async def test_transaction_rollback_on_nested_exception(test_date, day_repo):
    """Test that an exception in a nested transaction rolls back the entire transaction."""
    day = Day(
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    with pytest.raises(ValueError):
        async with TransactionManager():
            await day_repo.put(day)

            # Nested transaction - exception should rollback everything
            async with TransactionManager():
                day.status = DayStatus.UNSCHEDULED
                await day_repo.put(day)
                raise ValueError("Nested exception")

    # After rollback, nothing should be persisted
    from planned.core.exceptions import exceptions

    with pytest.raises(exceptions.NotFoundError):
        await day_repo.get(str(test_date))

