"""E2E tests for task routes."""

from uuid import uuid4

import pytest
from fastapi import status

from lykke.domain.entities import TaskEntity
from lykke.core.utils.dates import ensure_utc
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from lykke.infrastructure.repositories import TaskRepository


@pytest.mark.asyncio
async def test_complete_task_action(authenticated_client, test_date):
    """Test completing a task via the API.

    This is a regression test for a bug where completing a task would fail with:
    ValueError: 'TaskStatus.NOT_STARTED' is not a valid TaskStatus

    The bug was caused by using str(enum) instead of enum.value when serializing
    to the database, which produced 'TaskStatus.NOT_STARTED' instead of 'NOT_STARTED'.
    """
    client, user = await authenticated_client()

    # Ensure day exists by scheduling it
    from tests.e2e.conftest import schedule_day_for_user

    await schedule_day_for_user(user.id, test_date)

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test task for completion",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    # Verify task starts with NOT_STARTED status
    assert test_task.status == TaskStatus.NOT_STARTED

    # Complete the task via API
    response = client.post(
        f"/tasks/{test_task.id}/actions",
        json={"type": "COMPLETE"},
    )

    # Verify the response is successful
    assert response.status_code == status.HTTP_200_OK

    # Verify the task status changed to COMPLETE
    data = response.json()
    assert data["status"] == "COMPLETE"
    assert data["id"] == str(test_task.id)
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_punt_task_action(authenticated_client, test_date):
    """Test punting a task via the API."""
    client, user = await authenticated_client()

    # Ensure day exists by scheduling it
    from tests.e2e.conftest import schedule_day_for_user

    await schedule_day_for_user(user.id, test_date)

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task to Punt",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test task for punting",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    # Verify task starts with NOT_STARTED status
    assert test_task.status == TaskStatus.NOT_STARTED

    # Punt the task via API
    response = client.post(
        f"/tasks/{test_task.id}/actions",
        json={"type": "PUNT"},
    )

    # Verify the response is successful
    assert response.status_code == status.HTTP_200_OK

    # Verify the task status changed to PUNT
    data = response.json()
    assert data["status"] == "PUNT"
    assert data["id"] == str(test_task.id)


@pytest.mark.asyncio
async def test_snooze_task_action(authenticated_client, test_date):
    """Test snoozing a task via the API persists to DB."""
    client, user = await authenticated_client()

    # Ensure day exists by scheduling it
    from tests.e2e.conftest import schedule_day_for_user

    await schedule_day_for_user(user.id, test_date)

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task to Snooze",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test task for snoozing",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    snoozed_until = "2026-01-26T02:35:55.881Z"

    # Snooze the task via API
    response = client.post(
        f"/tasks/{test_task.id}/actions",
        json={"type": "SNOOZE", "data": {"snoozed_until": snoozed_until}},
    )

    # Verify the response is successful
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "SNOOZE"
    assert data["id"] == str(test_task.id)
    assert data["snoozed_until"] is not None

    persisted_task = await task_repo.get(test_task.id)
    assert persisted_task.status == TaskStatus.SNOOZE
    assert persisted_task.snoozed_until == ensure_utc(snoozed_until)
