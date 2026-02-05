"""Integration tests for Domain Event PubSub broadcasting."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from lykke.core.utils.domain_event_serialization import deserialize_domain_event
from lykke.domain.entities import AuditLogEntity, UserEntity
from lykke.domain.events.base import EntityCreatedEvent
from lykke.infrastructure.gateways import RedisPubSubGateway, StubPubSubGateway
from lykke.infrastructure.repositories import AuditLogRepository
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_audit_log_broadcast_on_commit(test_user: UserEntity) -> None:
    """Test that domain events are broadcasted via PubSub when entities are committed."""
    user_id = test_user.id

    # Create PubSub gateway
    pubsub_gateway = RedisPubSubGateway()

    # Subscribe to the user's domain-events channel using context manager
    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="domain-events"
    ) as subscription:
        # Give subscription a moment to be ready
        await asyncio.sleep(0.1)

        # Create an AuditLog entity through UnitOfWork
        task_id = uuid4()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type="TaskCompletedEvent",
            entity_id=task_id,
            entity_type="task",
            meta={"test": "data"},
        )

        # Commit the entity using UnitOfWork with PubSub gateway
        uow = SqlAlchemyUnitOfWork(user=test_user, pubsub_gateway=pubsub_gateway)
        async with uow:
            await uow.create(audit_log)

        # Try to receive the broadcasted message (now a domain event, not audit log)
        received_message = await subscription.get_message(timeout=2.0)

        # Verify the message was received and is a domain event
        assert received_message is not None

        # Deserialize as domain event
        domain_event = deserialize_domain_event(received_message)

        # Creating an AuditLogEntity emits EntityCreatedEvent
        assert isinstance(domain_event, EntityCreatedEvent)

        # Domain events don't have all the entity details - that's in the audit log itself
        # The event just signals that something was created

    # Clean up
    await pubsub_gateway.close()


@pytest.mark.asyncio
async def test_multiple_audit_logs_broadcast(test_user: UserEntity) -> None:
    """Test that multiple domain events are all broadcasted."""
    user_id = test_user.id

    pubsub_gateway = RedisPubSubGateway()

    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="domain-events"
    ) as subscription:
        await asyncio.sleep(0.1)

        # Create multiple AuditLog entities
        task1_id = uuid4()
        task2_id = uuid4()

        audit_log1 = AuditLogEntity(
            user_id=user_id,
            activity_type="TaskCompletedEvent",
            entity_id=task1_id,
            entity_type="task",
        )
        audit_log2 = AuditLogEntity(
            user_id=user_id,
            activity_type="TaskPuntedEvent",
            entity_id=task2_id,
            entity_type="task",
        )

        # Commit both entities in one transaction
        uow = SqlAlchemyUnitOfWork(user=test_user, pubsub_gateway=pubsub_gateway)
        async with uow:
            await uow.create(audit_log1)
            await uow.create(audit_log2)

        # Receive both messages (domain events)
        received_msg1 = await subscription.get_message(timeout=2.0)
        received_msg2 = await subscription.get_message(timeout=2.0)

        # Verify both messages were received
        assert received_msg1 is not None
        assert received_msg2 is not None

        # Deserialize as domain events
        event1 = deserialize_domain_event(received_msg1)
        event2 = deserialize_domain_event(received_msg2)

        # Both should be EntityCreatedEvent (creating audit logs)
        assert isinstance(event1, EntityCreatedEvent)
        assert isinstance(event2, EntityCreatedEvent)

        # The events signal that audit logs were created
        # The actual audit log data is stored in the database

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
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
    )

    # Commit with StubPubSubGateway (no broadcasting)
    uow = SqlAlchemyUnitOfWork(user=test_user, pubsub_gateway=StubPubSubGateway())
    async with uow:
        await uow.create(audit_log)

    # Verify the entity was saved to database
    audit_log_repo = AuditLogRepository(user=test_user)
    saved_log = await audit_log_repo.get(audit_log.id)
    assert saved_log.id == audit_log.id
    assert saved_log.activity_type == "TaskCompletedEvent"


@pytest.mark.asyncio
async def test_broadcast_only_on_successful_commit(test_user: UserEntity) -> None:
    """Test that AuditLog is NOT broadcasted if transaction fails."""
    user_id = test_user.id

    pubsub_gateway = RedisPubSubGateway()

    async with pubsub_gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="domain-events"
    ) as subscription:
        await asyncio.sleep(0.1)

        task_id = uuid4()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type="TaskCompletedEvent",
            entity_id=task_id,
            entity_type="task",
        )

        # Try to commit but raise an exception before commit
        uow = SqlAlchemyUnitOfWork(user=test_user, pubsub_gateway=pubsub_gateway)
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
    async with (
        pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="domain-events"
        ) as sub1,
        pubsub_gateway.subscribe_to_user_channel(
            user_id=user2_id, channel_type="domain-events"
        ) as sub2,
    ):
        await asyncio.sleep(0.1)

        # Create AuditLog for user1
        task_id = uuid4()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type="TaskCompletedEvent",
            entity_id=task_id,
            entity_type="task",
        )

        uow = SqlAlchemyUnitOfWork(user=test_user, pubsub_gateway=pubsub_gateway)
        async with uow:
            await uow.create(audit_log)

        # User1 should receive the message (domain event)
        received_msg1 = await sub1.get_message(timeout=2.0)
        assert received_msg1 is not None

        # Deserialize to verify it's a valid domain event
        event1 = deserialize_domain_event(received_msg1)
        assert isinstance(event1, EntityCreatedEvent)

        # User2 should NOT receive the message (isolated by user channel)
        received2 = await sub2.get_message(timeout=0.5)
        assert received2 is None

    # Clean up
    await pubsub_gateway.close()
