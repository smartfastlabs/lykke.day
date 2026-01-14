"""Integration tests for AuditLog PubSub broadcasting."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from lykke.domain.entities import AuditLogEntity, UserEntity
from lykke.domain.value_objects import ActivityType
from lykke.infrastructure.gateways import RedisPubSubGateway, StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_audit_log_broadcast_on_commit(test_user: UserEntity) -> None:
    """Test that AuditLog entities are broadcasted via PubSub when committed."""
    user_id = test_user.id
    
    # Create PubSub gateway
    pubsub_gateway = RedisPubSubGateway()

    # Subscribe to the user's auditlog channel using context manager
    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        # Give subscription a moment to be ready
        await asyncio.sleep(0.1)

        # Create an AuditLog entity through UnitOfWork
        task_id = uuid4()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_COMPLETED,
            entity_id=task_id,
            entity_type="task",
            meta={"test": "data"},
        )

        # Commit the entity using UnitOfWork with PubSub gateway
        uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=pubsub_gateway)
        async with uow:
            await uow.create(audit_log)

        # Try to receive the broadcasted message
        received = await subscription.get_message(timeout=2.0)

        # Verify the message was received
        assert received is not None
        assert received["id"] == str(audit_log.id)
        assert received["user_id"] == str(user_id)
        assert received["activity_type"] == "TASK_COMPLETED"
        assert received["entity_id"] == str(task_id)
        assert received["entity_type"] == "task"
        assert received["meta"]["test"] == "data"

    # Clean up
    await pubsub_gateway.close()


@pytest.mark.asyncio
async def test_multiple_audit_logs_broadcast(test_user: UserEntity) -> None:
    """Test that multiple AuditLog entities are all broadcasted."""
    user_id = test_user.id
    
    pubsub_gateway = RedisPubSubGateway()

    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        await asyncio.sleep(0.1)

        # Create multiple AuditLog entities
        task1_id = uuid4()
        task2_id = uuid4()

        audit_log1 = AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_COMPLETED,
            entity_id=task1_id,
            entity_type="task",
        )
        audit_log2 = AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_PUNTED,
            entity_id=task2_id,
            entity_type="task",
        )

        # Commit both entities in one transaction
        uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=pubsub_gateway)
        async with uow:
            await uow.create(audit_log1)
            await uow.create(audit_log2)

        # Receive both messages
        received1 = await subscription.get_message(timeout=2.0)
        received2 = await subscription.get_message(timeout=2.0)

        # Verify both messages were received
        assert received1 is not None
        assert received2 is not None

        # Verify the activity types (order might vary)
        activity_types = {received1["activity_type"], received2["activity_type"]}
        assert "TASK_COMPLETED" in activity_types
        assert "TASK_PUNTED" in activity_types

    # Clean up
    await pubsub_gateway.close()


@pytest.mark.asyncio
async def test_no_broadcast_without_pubsub_gateway(test_user: UserEntity) -> None:
    """Test that UnitOfWork works with StubPubSubGateway (no broadcasting).
    
    StubPubSubGateway is a no-op implementation that doesn't broadcast messages,
    useful for tests and background workers that don't need real-time broadcasting.
    """
    user_id = test_user.id
    
    # Create an AuditLog entity through UnitOfWork with StubPubSubGateway
    task_id = uuid4()
    audit_log = AuditLogEntity(
        user_id=user_id,
        activity_type=ActivityType.TASK_COMPLETED,
        entity_id=task_id,
        entity_type="task",
    )

    # Commit with StubPubSubGateway (no broadcasting)
    uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())
    async with uow:
        await uow.create(audit_log)

    # Verify the entity was saved to database
    uow_read = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())
    async with uow_read:
        saved_log = await uow_read.audit_log_ro_repo.get(audit_log.id)
        assert saved_log.id == audit_log.id
        assert saved_log.activity_type == ActivityType.TASK_COMPLETED


@pytest.mark.asyncio
async def test_broadcast_only_on_successful_commit(test_user: UserEntity) -> None:
    """Test that AuditLog is NOT broadcasted if transaction fails."""
    user_id = test_user.id
    
    pubsub_gateway = RedisPubSubGateway()

    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        await asyncio.sleep(0.1)

        task_id = uuid4()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type=ActivityType.TASK_COMPLETED,
            entity_id=task_id,
            entity_type="task",
        )

        # Try to commit but raise an exception before commit
        uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=pubsub_gateway)
        try:
            async with uow:
                await uow.create(audit_log)
                # Simulate an error before commit
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Try to receive a message (should timeout - no message sent)
        received = await subscription.get_message(timeout=0.5)

        assert received is None

    # Clean up
    await pubsub_gateway.close()


@pytest.mark.asyncio
async def test_user_isolation_in_broadcast(test_user: UserEntity) -> None:
    """Test that AuditLog broadcasts are isolated to specific users."""
    user_id = test_user.id
    
    # Create a second user (just use a different UUID for isolation test)
    user2_id = uuid4()

    pubsub_gateway = RedisPubSubGateway()

    # Subscribe to both users' channels
    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub1:
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user2_id, channel_type="auditlog"
        ) as sub2:
            await asyncio.sleep(0.1)

            # Create AuditLog for user1
            task_id = uuid4()
            audit_log = AuditLogEntity(
                user_id=user_id,
                activity_type=ActivityType.TASK_COMPLETED,
                entity_id=task_id,
                entity_type="task",
            )

            uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=pubsub_gateway)
            async with uow:
                await uow.create(audit_log)

            # User1 should receive the message
            received1 = await sub1.get_message(timeout=2.0)
            assert received1 is not None
            assert received1["user_id"] == str(user_id)

            # User2 should NOT receive the message
            received2 = await sub2.get_message(timeout=0.5)
            assert received2 is None

    # Clean up
    await pubsub_gateway.close()
