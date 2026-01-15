"""E2E tests for TaskCompletedEvent and TaskPuntedEvent in WebSocket sync."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.config import settings
from lykke.core.utils.audit_log_serialization import serialize_audit_log
from lykke.domain.entities import AuditLogEntity, TaskEntity
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.repositories import AuditLogRepository, TaskRepository


API_PREFIX = settings.API_PREFIX.rstrip("/")
WS_CONTEXT_PATH = (
    f"{API_PREFIX}/days/today/context" if API_PREFIX else "/days/today/context"
)


@pytest.mark.asyncio
async def test_task_completed_event_in_websocket_sync(authenticated_client, test_date):
    """Test that TaskCompletedEvent is properly handled in WebSocket sync responses."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Task to Complete",
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

        # Request full sync to establish baseline
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Wait a bit to ensure timestamps differ
        await asyncio.sleep(0.1)

        # Create TaskCompletedEvent audit log
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="TaskCompletedEvent",  # This is the key event type to test
            entity_id=test_task.id,
            entity_type="task",
            occurred_at=datetime.now(UTC),
            meta={
                "completed_at": datetime.now(UTC).isoformat(),
                "entity_data": {
                    "id": str(test_task.id),
                    "user_id": str(test_task.user_id),
                    "name": test_task.name,
                    "scheduled_date": test_task.scheduled_date.isoformat(),
                    "status": TaskStatus.COMPLETE.value,
                },
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Manually publish to Redis (simulating real-time broadcast)
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user.id,
            channel_type="auditlog",
            message=serialize_audit_log(audit_log),
        )

        # Wait for real-time event
        await asyncio.sleep(0.2)

        # Should receive sync_response with the TaskCompletedEvent as an "updated" change
        event = websocket.receive_json()
        assert event["type"] == "sync_response"
        assert event["changes"] is not None
        assert len(event["changes"]) > 0

        # Verify the change is for our task and is marked as "updated"
        task_change = next(
            (c for c in event["changes"] if c["entity_id"] == str(test_task.id)),
            None,
        )
        assert task_change is not None
        assert task_change["change_type"] == "updated"
        assert task_change["entity_type"] == "task"
        assert task_change["entity_data"] is not None
        assert task_change["entity_data"]["status"] == "COMPLETE"


@pytest.mark.asyncio
async def test_task_punted_event_in_websocket_sync(authenticated_client, test_date):
    """Test that TaskPuntedEvent is properly handled in WebSocket sync responses."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Task to Punt",
        status=TaskStatus.READY,
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

        # Request full sync to establish baseline
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"

        # Wait a bit to ensure timestamps differ
        await asyncio.sleep(0.1)

        # Create TaskPuntedEvent audit log
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="TaskPuntedEvent",  # This is the key event type to test
            entity_id=test_task.id,
            entity_type="task",
            occurred_at=datetime.now(UTC),
            meta={
                "old_status": TaskStatus.READY.value,
                "new_status": TaskStatus.PUNT.value,
                "entity_data": {
                    "id": str(test_task.id),
                    "user_id": str(test_task.user_id),
                    "name": test_task.name,
                    "scheduled_date": test_task.scheduled_date.isoformat(),
                    "status": TaskStatus.PUNT.value,
                },
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Manually publish to Redis (simulating real-time broadcast)
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user.id,
            channel_type="auditlog",
            message=serialize_audit_log(audit_log),
        )

        # Wait for real-time event
        await asyncio.sleep(0.2)

        # Should receive sync_response with the TaskPuntedEvent as an "updated" change
        event = websocket.receive_json()
        assert event["type"] == "sync_response"
        assert event["changes"] is not None
        assert len(event["changes"]) > 0

        # Verify the change is for our task and is marked as "updated"
        task_change = next(
            (c for c in event["changes"] if c["entity_id"] == str(test_task.id)),
            None,
        )
        assert task_change is not None
        assert task_change["change_type"] == "updated"
        assert task_change["entity_type"] == "task"
        assert task_change["entity_data"] is not None
        assert task_change["entity_data"]["status"] == "PUNT"


@pytest.mark.asyncio
async def test_incremental_sync_includes_task_state_events(
    authenticated_client, test_date
):
    """Test that incremental sync requests properly include TaskCompletedEvent and TaskPuntedEvent."""
    client, user = await authenticated_client()

    # Create a test task
    task_repo = TaskRepository(user_id=user.id)
    test_task = TaskEntity(
        id=uuid4(),
        user_id=user.id,
        name="Task for Incremental Sync",
        status=TaskStatus.READY,
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

        # Request full sync to get baseline timestamp
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = websocket.receive_json()
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Wait to ensure new events have later timestamps
        await asyncio.sleep(0.1)

        # Create TaskCompletedEvent audit log
        baseline_dt = datetime.fromisoformat(
            baseline_timestamp.replace("Z", "+00:00")
        )
        from datetime import timedelta

        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="TaskCompletedEvent",
            entity_id=test_task.id,
            entity_type="task",
            occurred_at=baseline_dt + timedelta(seconds=1),
            meta={
                "completed_at": (baseline_dt + timedelta(seconds=1)).isoformat(),
                "entity_data": {
                    "id": str(test_task.id),
                    "user_id": str(test_task.user_id),
                    "name": test_task.name,
                    "scheduled_date": test_task.scheduled_date.isoformat(),
                    "status": TaskStatus.COMPLETE.value,
                },
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Wait for audit log to be persisted
        await asyncio.sleep(0.1)

        # Request incremental sync
        incremental_sync = {
            "type": "sync_request",
            "since_timestamp": baseline_timestamp,
        }
        websocket.send_json(incremental_sync)

        # Should receive incremental response with TaskCompletedEvent
        incremental_response = websocket.receive_json()
        assert incremental_response["type"] == "sync_response"
        assert incremental_response["changes"] is not None
        assert len(incremental_response["changes"]) > 0

        # Verify TaskCompletedEvent is included as an "updated" change
        change_entity_ids = [
            change["entity_id"] for change in incremental_response["changes"]
        ]
        assert str(test_task.id) in change_entity_ids

        task_change = next(
            (
                c
                for c in incremental_response["changes"]
                if c["entity_id"] == str(test_task.id)
            ),
            None,
        )
        assert task_change is not None
        assert task_change["change_type"] == "updated"
