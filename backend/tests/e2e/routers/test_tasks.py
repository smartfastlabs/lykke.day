"""E2E tests for task routes."""

import asyncio
from uuid import uuid4

import pytest
from fastapi import status

from lykke.domain.entities import TaskEntity
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from lykke.infrastructure.gateways import RedisPubSubGateway
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
async def test_complete_task_broadcasts_audit_log(authenticated_client, test_date):
    """Test that completing a task via API broadcasts audit log to PubSub.

    This is a regression test for a bug where the UnitOfWorkFactory
    was not initialized with a PubSubGateway, causing audit logs
    to not be broadcast when tasks were completed via the API.
    """
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task for PubSub",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test task for PubSub broadcast",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    # Set up PubSub subscription BEFORE making the API call
    pubsub_gateway = RedisPubSubGateway()

    try:
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user.id, channel_type="auditlog"
        ) as subscription:
            # Give subscription a moment to be ready
            await asyncio.sleep(0.1)

            # Complete the task via API
            response = client.post(
                f"/tasks/{test_task.id}/actions",
                json={"type": "COMPLETE"},
            )

            # Verify the API call was successful
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "COMPLETE"

            # Verify the audit log was broadcast via PubSub
            # We may receive EntityCreatedEvent from task creation first,
            # so we need to keep getting messages until we find TaskCompletedEvent
            received = None
            max_attempts = 10
            for _ in range(max_attempts):
                msg = await subscription.get_message(timeout=2.0)
                if msg is None:
                    break
                # Skip EntityCreatedEvent from task creation
                if msg.get("activity_type") == "TaskCompletedEvent":
                    received = msg
                    break

            # This assertion would fail before the fix because
            # get_unit_of_work_factory() wasn't passing pubsub_gateway
            assert received is not None, (
                "TaskCompletedEvent audit log was not broadcast via PubSub. "
                "This likely means the UnitOfWorkFactory was not "
                "initialized with a PubSubGateway."
            )

            # Verify the broadcast message content
            assert received["activity_type"] == "TaskCompletedEvent"
            assert received["entity_id"] == str(test_task.id)
            assert received["entity_type"] == "task"
            assert received["user_id"] == str(user.id)
    finally:
        await pubsub_gateway.close()


@pytest.mark.asyncio
async def test_punt_task_broadcasts_audit_log(authenticated_client, test_date):
    """Test that punting a task via API broadcasts audit log to PubSub."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task for Punt PubSub",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        description="Test task for punt PubSub broadcast",
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    # Set up PubSub subscription BEFORE making the API call
    pubsub_gateway = RedisPubSubGateway()

    try:
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user.id, channel_type="auditlog"
        ) as subscription:
            # Give subscription a moment to be ready
            await asyncio.sleep(0.1)

            # Punt the task via API
            response = client.post(
                f"/tasks/{test_task.id}/actions",
                json={"type": "PUNT"},
            )

            # Verify the API call was successful
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "PUNT"

            # Verify the audit log was broadcast via PubSub
            # We may receive EntityCreatedEvent from task creation first,
            # so we need to keep getting messages until we find TaskPuntedEvent
            received = None
            max_attempts = 10
            for _ in range(max_attempts):
                msg = await subscription.get_message(timeout=2.0)
                if msg is None:
                    break
                # Skip EntityCreatedEvent from task creation
                if msg.get("activity_type") == "TaskPuntedEvent":
                    received = msg
                    break

            assert received is not None, (
                "TaskPuntedEvent audit log was not broadcast via PubSub for punt action. "
                "This likely means the UnitOfWorkFactory was not "
                "initialized with a PubSubGateway."
            )

            # Verify the broadcast message content
            assert received["activity_type"] == "TaskPuntedEvent"
            assert received["entity_id"] == str(test_task.id)
            assert received["entity_type"] == "task"
            assert received["user_id"] == str(user.id)
    finally:
        await pubsub_gateway.close()
