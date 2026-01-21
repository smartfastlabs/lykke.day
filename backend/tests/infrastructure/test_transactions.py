"""Tests for transaction management."""

from uuid import uuid4

import pytest
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity
from lykke.infrastructure.database.transaction import (
    TransactionManager,
    get_transaction_connection,
)
from lykke.core.utils.dates import get_current_datetime


@pytest.mark.asyncio
async def test_transaction_commits_on_success(test_date, test_user, day_repo):
    """Test that a transaction commits successfully when no exception occurs."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    async with TransactionManager():
        await day_repo.put(day)

    # After transaction commits, the day should be retrievable
    day_id = DayEntity.id_from_date_and_user(test_date, test_user.id)
    result = await day_repo.get(day_id)
    assert result.status == value_objects.DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_transaction_rolls_back_on_exception(test_date, test_user, day_repo):
    """Test that a transaction rolls back when an exception occurs."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    with pytest.raises(ValueError):
        async with TransactionManager():
            await day_repo.put(day)
            raise ValueError("Test exception")

    # After rollback, the day should not be in the database
    day_id = DayEntity.id_from_date_and_user(test_date, test_user.id)
    with pytest.raises(NotFoundError):
        await day_repo.get(day_id)


@pytest.mark.asyncio
async def test_repository_works_without_transaction(test_date, test_user, day_repo):
    """Test that repositories work correctly without an active transaction."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    # No transaction - should create its own connection
    await day_repo.put(day)

    day_id = DayEntity.id_from_date_and_user(test_date, test_user.id)
    result = await day_repo.get(day_id)
    assert result.status == value_objects.DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_read_operations_see_uncommitted_changes(test_date, test_user, day_repo):
    """Test that read operations within a transaction see uncommitted changes."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    async with TransactionManager():
        # Put the day in the transaction
        await day_repo.put(day)

        # Read it back - should see the uncommitted change
        result = await day_repo.get(day.id)
        assert result.status == value_objects.DayStatus.SCHEDULED

        # Update it
        day.status = value_objects.DayStatus.UNSCHEDULED
        await day_repo.put(day)

        # Read it again - should see the updated uncommitted change
        result = await day_repo.get(day.id)
        assert result.status == value_objects.DayStatus.UNSCHEDULED

    # After commit, the final state should be persisted
    result = await day_repo.get(day.id)
    assert result.status == value_objects.DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_multiple_operations_in_single_transaction(
    test_date, test_user, day_repo, task_repo
):
    """Test that multiple operations in a single transaction are atomic."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    task = TaskEntity(
        user_id=test_user.id,
        name="Test Task",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.ACTIVITY,
        description="Test",
        category=value_objects.TaskCategory.HOUSE,
        frequency=value_objects.TaskFrequency.DAILY,
        scheduled_date=test_date,
    )

    async with TransactionManager():
        await day_repo.put(day)
        await task_repo.put(task)

    # Both should be committed
    result_day = await day_repo.get(day.id)
    assert result_day.status == value_objects.DayStatus.SCHEDULED

    # Find the task
    tasks = await task_repo.search(value_objects.TaskQuery(date=test_date))
    assert len(tasks) == 1
    assert tasks[0].name == "Test Task"


@pytest.mark.asyncio
async def test_nested_transactions_reuse_connection(test_date, test_user, day_repo):
    """Test that nested transactions reuse the same connection."""
    day1 = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
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
            day1.status = value_objects.DayStatus.UNSCHEDULED
            await day_repo.put(day1)

    # After commit, the final state should be persisted
    result = await day_repo.get(day1.id)
    assert result.status == value_objects.DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_transaction_connection_is_none_outside_transaction():
    """Test that get_transaction_connection returns None when no transaction is active."""
    conn = get_transaction_connection()
    assert conn is None


@pytest.mark.asyncio
async def test_transaction_rollback_on_nested_exception(test_date, test_user, day_repo):
    """Test that an exception in a nested transaction rolls back the entire transaction."""
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
    )

    with pytest.raises(ValueError):
        async with TransactionManager():
            await day_repo.put(day)

            # Nested transaction - exception should rollback everything
            async with TransactionManager():
                day.status = value_objects.DayStatus.UNSCHEDULED
                await day_repo.put(day)
                raise ValueError("Nested exception")

    # After rollback, nothing should be persisted
    with pytest.raises(NotFoundError):
        await day_repo.get(day.id)
