"""E2E tests for routines WebSocket real-time updates."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from lykke.core.config import settings
from lykke.core.utils.audit_log_serialization import serialize_audit_log
from lykke.domain.entities import AuditLogEntity, RoutineEntity
from lykke.domain.value_objects.routine import RoutineSchedule
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.repositories import AuditLogRepository, RoutineRepository

API_PREFIX = settings.API_PREFIX.rstrip("/")
WS_CONTEXT_PATH = (
    f"{API_PREFIX}/days/today/context" if API_PREFIX else "/days/today/context"
)


async def receive_json_with_timeout(websocket, timeout: float = 5.0):
    """Receive JSON from WebSocket with timeout to prevent hanging tests.

    Args:
        websocket: The WebSocket connection
        timeout: Maximum time to wait in seconds (default: 5.0)

    Returns:
        The received JSON message

    Raises:
        asyncio.TimeoutError: If no message is received within the timeout
    """
    return await asyncio.wait_for(
        asyncio.to_thread(websocket.receive_json),
        timeout=timeout,
    )


@pytest.mark.asyncio
async def test_realtime_routine_creation_notification(authenticated_client, test_date):
    """Test that routine creation triggers real-time notifications via WebSocket."""
    client, user = await authenticated_client()

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = await receive_json_with_timeout(websocket)
        assert ack["type"] == "connection_ack"

        # Request full sync to establish connection
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = await receive_json_with_timeout(websocket)
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Wait a bit to ensure new audit logs have later timestamps
        await asyncio.sleep(0.1)

        # Create a routine via API (simulating another client)
        routine_repo = RoutineRepository(user_id=user.id)
        new_routine = RoutineEntity(
            id=uuid4(),
            user_id=user.id,
            name="New Routine",
            category=TaskCategory.HOUSE,
            description="Test description",
            routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
            tasks=[],
        )
        new_routine = await routine_repo.put(new_routine)

        # Create audit log (routines are now auditable)
        baseline_dt = datetime.fromisoformat(baseline_timestamp.replace("Z", "+00:00"))
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="EntityCreatedEvent",
            entity_id=new_routine.id,
            entity_type="routine",
            occurred_at=baseline_dt + timedelta(seconds=1),
            meta={
                "entity_data": {
                    "id": str(new_routine.id),
                    "user_id": str(new_routine.user_id),
                    "name": new_routine.name,
                    "category": new_routine.category.value,
                    "description": new_routine.description,
                    "routine_schedule": {
                        "frequency": new_routine.routine_schedule.frequency.value,
                    },
                    "tasks": [],
                }
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Publish to Redis
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user.id,
            channel_type="auditlog",
            message=serialize_audit_log(audit_log),
        )

        # Wait for real-time event
        await asyncio.sleep(0.2)

        try:
            # The backend should send a sync_response with routine change
            event = await receive_json_with_timeout(websocket)
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our routine
            change_entity_ids = [change["entity_id"] for change in event["changes"]]
            assert str(new_routine.id) in change_entity_ids

            # Verify the change includes entity data
            routine_change = next(
                (c for c in event["changes"] if c["entity_id"] == str(new_routine.id)),
                None,
            )
            assert routine_change is not None
            assert routine_change["change_type"] == "created"
            assert routine_change["entity_type"] == "routine"
            assert routine_change["entity_data"] is not None
            assert routine_change["entity_data"]["name"] == "New Routine"
        except Exception as e:
            pytest.fail(f"No real-time event received after routine creation: {e}")


@pytest.mark.asyncio
async def test_realtime_routine_update_notification(authenticated_client, test_date):
    """Test that routine updates trigger real-time notifications via WebSocket."""
    client, user = await authenticated_client()

    # Create a routine first
    routine_repo = RoutineRepository(user_id=user.id)
    test_routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Initial description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    test_routine = await routine_repo.put(test_routine)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = await receive_json_with_timeout(websocket)
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = await receive_json_with_timeout(websocket)
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Wait a bit
        await asyncio.sleep(0.1)

        # Update the routine
        test_routine.name = "Updated Routine Name"
        test_routine.description = "Updated description"
        updated_routine = await routine_repo.put(test_routine)

        # Create audit log for update
        baseline_dt = datetime.fromisoformat(baseline_timestamp.replace("Z", "+00:00"))
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="EntityUpdatedEvent",
            entity_id=updated_routine.id,
            entity_type="routine",
            occurred_at=baseline_dt + timedelta(seconds=1),
            meta={
                "entity_data": {
                    "id": str(updated_routine.id),
                    "user_id": str(updated_routine.user_id),
                    "name": updated_routine.name,
                    "category": updated_routine.category.value,
                    "description": updated_routine.description,
                    "routine_schedule": {
                        "frequency": updated_routine.routine_schedule.frequency.value,
                    },
                    "tasks": [],
                }
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Publish to Redis
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user.id,
            channel_type="auditlog",
            message=serialize_audit_log(audit_log),
        )

        # Wait for real-time event
        await asyncio.sleep(0.2)

        try:
            # The backend should send a sync_response with routine change
            event = await receive_json_with_timeout(websocket)
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our routine
            routine_change = next(
                (c for c in event["changes"] if c["entity_id"] == str(test_routine.id)),
                None,
            )
            assert routine_change is not None
            assert routine_change["change_type"] == "updated"
            assert routine_change["entity_type"] == "routine"
            assert routine_change["entity_data"] is not None
            assert routine_change["entity_data"]["name"] == "Updated Routine Name"
        except Exception as e:
            pytest.fail(f"No real-time event received after routine update: {e}")


@pytest.mark.asyncio
async def test_realtime_routine_deletion_notification(authenticated_client, test_date):
    """Test that routine deletion triggers real-time notifications via WebSocket."""
    client, user = await authenticated_client()

    # Create a routine first
    routine_repo = RoutineRepository(user_id=user.id)
    test_routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Routine to Delete",
        category=TaskCategory.HOUSE,
        description="Will be deleted",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    test_routine = await routine_repo.put(test_routine)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = await receive_json_with_timeout(websocket)
        assert ack["type"] == "connection_ack"

        # Request full sync
        sync_request = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(sync_request)
        sync_response = await receive_json_with_timeout(websocket)
        assert sync_response["type"] == "sync_response"
        baseline_timestamp = sync_response["last_audit_log_timestamp"]

        # Wait a bit
        await asyncio.sleep(0.1)

        # Delete the routine
        await routine_repo.delete(test_routine.id)

        # Create audit log for deletion
        # Note: Must include entity_data in meta for filtering to work,
        # even though deleted entities don't include entity_data in the response
        baseline_dt = datetime.fromisoformat(baseline_timestamp.replace("Z", "+00:00"))
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="EntityDeletedEvent",
            entity_id=test_routine.id,
            entity_type="routine",
            occurred_at=baseline_dt + timedelta(seconds=1),
            meta={
                "entity_data": {
                    "id": str(test_routine.id),
                    "user_id": str(test_routine.user_id),
                    "name": test_routine.name,
                    "category": test_routine.category.value,
                    "description": test_routine.description,
                    "routine_schedule": {
                        "frequency": test_routine.routine_schedule.frequency.value,
                    },
                    "tasks": [],
                }
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Publish to Redis
        redis_pool = getattr(client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user.id,
            channel_type="auditlog",
            message=serialize_audit_log(audit_log),
        )

        # Wait for real-time event
        await asyncio.sleep(0.2)

        try:
            # The backend should send a sync_response with routine deletion
            event = await receive_json_with_timeout(websocket, timeout=5.0)
            assert event["type"] == "sync_response"
            assert event["changes"] is not None
            assert len(event["changes"]) > 0

            # Verify the change is for our routine
            routine_change = next(
                (c for c in event["changes"] if c["entity_id"] == str(test_routine.id)),
                None,
            )
            assert routine_change is not None
            assert routine_change["change_type"] == "deleted"
            assert routine_change["entity_type"] == "routine"
            # Deleted entities don't include entity_data
            assert routine_change["entity_data"] is None
        except asyncio.TimeoutError:
            pytest.fail(
                "No real-time event received after routine deletion: "
                "Timeout waiting for WebSocket message. "
                "The deletion event may not have been published or processed."
            )
        except AssertionError as e:
            pytest.fail(
                f"Real-time event received but assertion failed: {e}. "
                f"Event received: {event if 'event' in locals() else 'None'}"
            )
        except Exception as e:
            pytest.fail(
                f"No real-time event received after routine deletion: {type(e).__name__}: {e}"
            )


@pytest.mark.asyncio
async def test_routine_incremental_sync(authenticated_client, test_date):
    """Test that routines are included in incremental sync responses."""
    client, user = await authenticated_client()

    # Create a routine before baseline
    routine_repo = RoutineRepository(user_id=user.id)
    initial_routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Initial Routine",
        category=TaskCategory.HOUSE,
        description="Before baseline",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    initial_routine = await routine_repo.put(initial_routine)

    with client.websocket_connect(f"{WS_CONTEXT_PATH}?token={user.id}") as websocket:
        # Receive connection ack
        ack = await receive_json_with_timeout(websocket)
        assert ack["type"] == "connection_ack"

        # Request full sync to establish baseline
        full_sync = {"type": "sync_request", "since_timestamp": None}
        websocket.send_json(full_sync)
        full_response = await receive_json_with_timeout(websocket)
        assert full_response["type"] == "sync_response"
        baseline_timestamp = full_response["last_audit_log_timestamp"]

        # Wait a bit
        await asyncio.sleep(0.1)

        # Create a new routine after baseline
        new_routine = RoutineEntity(
            id=uuid4(),
            user_id=user.id,
            name="New Routine After Baseline",
            category=TaskCategory.HOUSE,
            description="Created after baseline",
            routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
            tasks=[],
        )
        new_routine = await routine_repo.put(new_routine)

        # Create audit log
        baseline_dt = datetime.fromisoformat(baseline_timestamp.replace("Z", "+00:00"))
        audit_log = AuditLogEntity(
            user_id=user.id,
            activity_type="EntityCreatedEvent",
            entity_id=new_routine.id,
            entity_type="routine",
            occurred_at=baseline_dt + timedelta(seconds=1),
            meta={
                "entity_data": {
                    "id": str(new_routine.id),
                    "user_id": str(new_routine.user_id),
                    "name": new_routine.name,
                    "category": new_routine.category.value,
                    "description": new_routine.description,
                    "routine_schedule": {
                        "frequency": new_routine.routine_schedule.frequency.value,
                    },
                    "tasks": [],
                }
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user.id)
        await audit_log_repo.put(audit_log)

        # Request incremental sync
        incremental_sync = {
            "type": "sync_request",
            "since_timestamp": baseline_timestamp,
        }
        websocket.send_json(incremental_sync)

        # Receive incremental response
        incremental_response = await receive_json_with_timeout(websocket)
        assert incremental_response["type"] == "sync_response"
        assert incremental_response["changes"] is not None

        # Verify the new routine is in the incremental changes
        change_entity_ids = [
            change["entity_id"] for change in incremental_response["changes"]
        ]
        assert str(new_routine.id) in change_entity_ids

        # Verify the routine change includes entity data
        routine_change = next(
            (
                c
                for c in incremental_response["changes"]
                if c["entity_id"] == str(new_routine.id)
            ),
            None,
        )
        assert routine_change is not None
        assert routine_change["change_type"] == "created"
        assert routine_change["entity_type"] == "routine"
        assert routine_change["entity_data"] is not None
        assert routine_change["entity_data"]["name"] == "New Routine After Baseline"
