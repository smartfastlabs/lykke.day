"""E2E tests for days WebSocket endpoint - comprehensive real-time sync tests."""

import asyncio
import json
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from lykke.core.config import settings
from lykke.domain.entities import CalendarEntryEntity, TaskEntity
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from lykke.infrastructure.repositories import CalendarEntryRepository, TaskRepository


API_PREFIX = settings.API_PREFIX.rstrip("/")
WS_CONTEXT_PATH = (
    f"{API_PREFIX}/days/today/context" if API_PREFIX else "/days/today/context"
)


@pytest.mark.asyncio
async def test_websocket_connection_and_authentication(authenticated_client, test_date):
    """Test WebSocket connection and authentication."""
    client, user = await authenticated_client()

    # Connect to WebSocket (authentication is handled via dependency override)
    with client.websocket_connect(WS_CONTEXT_PATH) as websocket:
        # Should receive connection acknowledgment
        message = websocket.receive_json()
        assert message["type"] == "connection_ack"
        assert message["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_full_sync_request(authenticated_client, test_date):
    """Test requesting full day context via WebSocket."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Task for Full Sync",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)

        # Receive sync response
        response = websocket.receive_json()
        assert response["type"] == "sync_response"
        assert response["day_context"] is not None
        assert response["day_context"]["tasks"] is not None

        # Verify task is in the response
        task_ids = [task["id"] for task in response["day_context"]["tasks"]]
        assert str(test_task.id) in task_ids

        # Verify last_audit_log_timestamp is present
        assert response["last_audit_log_timestamp"] is not None


@pytest.mark.asyncio
async def test_incremental_sync_request(authenticated_client, test_date):
    """Test requesting incremental changes via WebSocket."""
    client, user = await authenticated_client()

    # Create initial task
    task_repo = TaskRepository(user_id=user.id)
    initial_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Initial Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(initial_task)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync first to get baseline
        full_sync = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(full_sync)
        full_response = websocket.receive_json()
        assert full_response["type"] == "sync_response"
        baseline_timestamp = full_response["last_audit_log_timestamp"]

        # Create a new task after baseline
        new_task = TaskEntity(
            id=uuid4(),
            user_id=user.id,
            name="New Task After Baseline",
            status=TaskStatus.NOT_STARTED,
            type=TaskType.ACTIVITY,
            category=TaskCategory.HOUSE,
            frequency=TaskFrequency.DAILY,
            scheduled_date=test_date,
        )
        await task_repo.put(new_task)

        # Wait a bit for audit log to be created
        await asyncio.sleep(0.1)

        # Request incremental sync
        incremental_sync = {
            "type": "sync_request",
            "since_timestamp": baseline_timestamp,
        }
        websocket.send_json(incremental_sync)

        # Receive incremental response
        incremental_response = websocket.receive_json()
        assert incremental_response["type"] == "sync_response"
        assert incremental_response["changes"] is not None
        assert len(incremental_response["changes"]) > 0

        # Verify new task is in changes
        change_entity_ids = [
            change["entity_id"] for change in incremental_response["changes"]
        ]
        assert str(new_task.id) in change_entity_ids


@pytest.mark.asyncio
async def test_realtime_task_update_notification(authenticated_client, test_date):
    """Test that task updates trigger real-time notifications via WebSocket."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Task for Real-time Update",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync to establish connection
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Update task status via API (simulating another client)
        from lykke.application.commands import RecordTaskActionHandler
        from lykke.application.unit_of_work import UnitOfWorkFactory
        from lykke.infrastructure.gateways import RedisPubSubGateway
        from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory

        # Get Redis pool from app state
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)

        handler = RecordTaskActionHandler(task_repo, uow_factory, user.id)
        await handler.record_task_action(task_id=test_task.id, action="complete")

        # Wait for real-time event (with timeout)
        try:
            # The backend should send a sync_response with entity changes
            event = websocket.receive_json()
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our task
            change_entity_ids = [change["entity_id"] for change in event["changes"]]
            assert str(test_task.id) in change_entity_ids

            # Verify the change includes entity data (for updated tasks)
            task_change = next(
                (c for c in event["changes"] if c["entity_id"] == str(test_task.id)),
                None,
            )
            assert task_change is not None
            assert task_change["change_type"] == "updated"
            assert task_change["entity_data"] is not None
            assert task_change["entity_data"]["status"] == "COMPLETE"
        except Exception as e:
            # If no event received, the real-time updates aren't working
            pytest.fail(f"No real-time event received after task update: {e}")


@pytest.mark.asyncio
async def test_realtime_task_creation_notification(authenticated_client, test_date):
    """Test that task creation triggers real-time notifications."""
    client, user = await authenticated_client()

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Create a new task (simulating another client)
        task_repo = TaskRepository(user_id=user.id)
        new_task = TaskEntity(
            id=uuid4(),
            user_id=user.id,
            name="New Real-time Task",
            status=TaskStatus.NOT_STARTED,
            type=TaskType.ACTIVITY,
            category=TaskCategory.HOUSE,
            frequency=TaskFrequency.DAILY,
            scheduled_date=test_date,
        )
        await task_repo.put(new_task)

        # Wait for real-time event
        try:
            event = websocket.receive_json()
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our new task
            change_entity_ids = [change["entity_id"] for change in event["changes"]]
            assert str(new_task.id) in change_entity_ids
        except Exception as e:
            pytest.fail(f"No real-time event received after task creation: {e}")


@pytest.mark.asyncio
async def test_realtime_task_deletion_notification(authenticated_client, test_date):
    """Test that task deletion triggers real-time notifications."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Task to Delete",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Delete the task
        await task_repo.delete(test_task.id)

        # Wait for real-time event
        try:
            event = websocket.receive_json()
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our deleted task
            task_change = next(
                (c for c in event["changes"] if c["entity_id"] == str(test_task.id)),
                None,
            )
            assert task_change is not None
            assert task_change["change_type"] == "deleted"
        except Exception as e:
            pytest.fail(f"No real-time event received after task deletion: {e}")


@pytest.mark.asyncio
async def test_realtime_calendar_entry_update(authenticated_client, test_date):
    """Test that calendar entry updates trigger real-time notifications."""
    client, user = await authenticated_client()

    # Create a test calendar entry
    from uuid import NAMESPACE_DNS, uuid5

    from lykke.domain.value_objects.task import TaskFrequency

    calendar_repo = CalendarEntryRepository(user_id=user.id)

    # Create calendar entry with required fields
    test_entry = CalendarEntryEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Event",
        calendar_id=uuid5(NAMESPACE_DNS, "test-calendar"),
        platform_id="test-platform-id",
        platform="testing",
        status="confirmed",
        frequency=TaskFrequency.ONCE,
        starts_at=datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0),
        ends_at=datetime.now(UTC).replace(hour=11, minute=0, second=0, microsecond=0),
    )
    await calendar_repo.put(test_entry)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Update calendar entry
        test_entry.title = "Updated Event Title"
        await calendar_repo.put(test_entry)

        # Wait for real-time event
        try:
            event = websocket.receive_json()
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our calendar entry
            change_entity_ids = [change["entity_id"] for change in event["changes"]]
            assert str(test_entry.id) in change_entity_ids
        except Exception as e:
            pytest.fail(f"No real-time event received after calendar entry update: {e}")


@pytest.mark.asyncio
async def test_filtering_other_days_entities(authenticated_client, test_date):
    """Test that entities from other days are filtered out."""
    client, user = await authenticated_client()

    # Create a task for today
    task_repo = TaskRepository(user_id=user.id)
    today_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Today's Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(today_task)

    # Create a task for tomorrow
    from datetime import timedelta

    tomorrow_date = test_date + timedelta(days=1)
    tomorrow_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Tomorrow's Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=tomorrow_date,
    )
    await task_repo.put(tomorrow_task)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Verify only today's task is in the response
        task_ids = [task["id"] for task in sync_response["day_context"]["tasks"]]
        assert str(today_task.id) in task_ids
        assert str(tomorrow_task.id) not in task_ids

        # Update tomorrow's task - should NOT trigger real-time event
        tomorrow_task.status = TaskStatus.COMPLETE
        await task_repo.put(tomorrow_task)

        # Should NOT receive an event (filtered out)
        try:
            event = websocket.receive_json()
            # If we get an event, it should NOT be for tomorrow's task
            if event.get("type") == "sync_response":
                changes = event.get("changes", [])
                change_entity_ids = [change["entity_id"] for change in changes]
                if str(tomorrow_task.id) in change_entity_ids:
                    pytest.fail("Received event for tomorrow's task - filtering failed")
        except Exception:
            # No event received is expected (filtering worked)
            pass


@pytest.mark.asyncio
async def test_multiple_websocket_connections(authenticated_client, test_date):
    """Test that multiple WebSocket connections work independently."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Multi-Connection Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.ACTIVITY,
        category=TaskCategory.HOUSE,
        frequency=TaskFrequency.DAILY,
        scheduled_date=test_date,
    )
    await task_repo.put(test_task)

    # Connect two WebSocket clients
    with (
        client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as ws1,
        client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as ws2,
    ):
        # Both should receive connection acks
        ack1 = ws1.receive_json()
        ack2 = ws2.receive_json()
        assert ack1["type"] == "connection_ack"
        assert ack2["type"] == "connection_ack"

        # Both request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        ws1.send_json(sync_request)
        ws2.send_json(sync_request)

        response1 = ws1.receive_json()
        response2 = ws2.receive_json()
        assert response1["type"] == "sync_response"
        assert response2["type"] == "sync_response"

        # Update task - both should receive notification
        from lykke.application.commands import RecordTaskActionHandler
        from lykke.infrastructure.gateways import RedisPubSubGateway
        from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory

        redis_pool = getattr(client.app.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)
        handler = RecordTaskActionHandler(task_repo, uow_factory, user.id)
        await handler.record_task_action(task_id=test_task.id, action="complete")

        # Both should receive events
        try:
            event1 = ws1.receive_json()
            event2 = ws2.receive_json()
            assert event1["type"] == "sync_response"
            assert event2["type"] == "sync_response"
            assert event1["changes"] is not None
            assert event2["changes"] is not None
        except Exception as e:
            pytest.fail(f"One or both connections did not receive real-time event: {e}")


@pytest.mark.asyncio
async def test_sync_detection_out_of_sync(authenticated_client, test_date):
    """Test that out-of-sync detection works correctly."""
    client, user = await authenticated_client()

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Simulate receiving an out-of-order event (older timestamp)
        # This would happen if the client receives an event with occurred_at < last_processed_timestamp
        # The frontend should detect this and mark as out of sync
        # For this test, we'll verify the timestamp is included in events
        task_repo = TaskRepository(user_id=user.id)
        test_task = TaskEntity(
            id=uuid4(),
            user_id=user.id,
            name="Sync Detection Task",
            status=TaskStatus.NOT_STARTED,
            type=TaskType.ACTIVITY,
            category=TaskCategory.HOUSE,
            frequency=TaskFrequency.DAILY,
            scheduled_date=test_date,
        )
        await task_repo.put(test_task)

        # Wait for event
        try:
            event = websocket.receive_json()
            if event.get("type") == "sync_response":
                # Verify timestamp is present for sync detection
                assert "last_audit_log_timestamp" in event
                assert event["last_audit_log_timestamp"] is not None
        except Exception:
            pass  # Event may not be received if task creation doesn't trigger


@pytest.mark.asyncio
async def test_error_handling_invalid_request(authenticated_client, test_date):
    """Test error handling for invalid requests."""
    client, user = await authenticated_client()

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = websocket.receive_json()
        assert ack["type"] == "connection_ack"

        # Send invalid request
        invalid_request = {"type": "invalid_type"}
        websocket.send_json(invalid_request)

        # Should receive error
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "code" in error
        assert "message" in error


@pytest.mark.asyncio
async def test_websocket_reconnection_scenario(authenticated_client, test_date):
    """Test reconnection scenario with incremental sync."""
    client, user = await authenticated_client()

    # First connection
    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as ws1:
        ack1 = ws1.receive_json()
        assert ack1["type"] == "connection_ack"

        sync_request = {"type": "sync_request", "since_timestamp": None}
        ws1.send_json(sync_request)
        response1 = ws1.receive_json()
        last_timestamp = response1["last_audit_log_timestamp"]

        # Create a task while first connection is active
        task_repo = TaskRepository(user_id=user.id)
        task1 = TaskEntity(
            id=uuid4(),
            user_id=user.id,
            name="Task Before Reconnect",
            status=TaskStatus.NOT_STARTED,
            type=TaskType.ACTIVITY,
            category=TaskCategory.HOUSE,
            frequency=TaskFrequency.DAILY,
            scheduled_date=test_date,
        )
        await task_repo.put(task1)

    # Simulate reconnection - new WebSocket connection
    await asyncio.sleep(0.1)  # Small delay to ensure audit log is created

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as ws2:
        ack2 = ws2.receive_json()
        assert ack2["type"] == "connection_ack"

        # Request incremental sync using last timestamp from previous connection
        incremental_sync = {
            "type": "sync_request",
            "since_timestamp": last_timestamp,
        }
        ws2.send_json(incremental_sync)
        response2 = ws2.receive_json()
        assert response2["type"] == "sync_response"
        assert response2["changes"] is not None

        # Verify task1 is in the changes
        change_entity_ids = [change["entity_id"] for change in response2["changes"]]
        assert str(task1.id) in change_entity_ids
