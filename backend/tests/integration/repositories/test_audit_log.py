"""Integration tests for AuditLogRepository."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import AuditLogEntity
from lykke.domain.value_objects.query import AuditLogQuery
from lykke.infrastructure.repositories import AuditLogRepository


@pytest.mark.asyncio
async def test_get(audit_log_repo, test_user):
    """Test getting an audit log by ID."""
    task_id = uuid4()
    audit_log = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
        meta={"test": "data"},
    )
    await audit_log_repo.put(audit_log)

    result = await audit_log_repo.get(audit_log.id)

    assert result.id == audit_log.id
    assert result.user_id == test_user.id
    assert result.activity_type == "TaskCompletedEvent"
    assert result.entity_id == task_id
    assert result.entity_type == "task"
    assert result.meta == {"test": "data"}


@pytest.mark.asyncio
async def test_get_not_found(audit_log_repo):
    """Test getting a non-existent audit log raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await audit_log_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(audit_log_repo, test_user):
    """Test creating a new audit log."""
    task_id = uuid4()
    audit_log = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
        meta={"action": "completed"},
    )

    result = await audit_log_repo.put(audit_log)

    assert result.id == audit_log.id
    assert result.user_id == test_user.id
    assert result.activity_type == "TaskCompletedEvent"
    assert result.entity_id == task_id
    assert result.meta == {"action": "completed"}


@pytest.mark.asyncio
async def test_search_by_activity_type(audit_log_repo, test_user):
    """Test searching audit logs by activity type."""
    task_id1 = uuid4()
    task_id2 = uuid4()
    task_id3 = uuid4()

    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id1,
        entity_type="task",
    )
    log2 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskPuntedEvent",
        entity_id=task_id2,
        entity_type="task",
    )
    log3 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id3,
        entity_type="task",
    )

    await audit_log_repo.put(log1)
    await audit_log_repo.put(log2)
    await audit_log_repo.put(log3)

    results = await audit_log_repo.search(
        AuditLogQuery(activity_type="TaskCompletedEvent")
    )

    assert len(results) == 2
    result_ids = [r.id for r in results]
    assert log1.id in result_ids
    assert log3.id in result_ids
    assert log2.id not in result_ids


@pytest.mark.asyncio
async def test_search_by_entity_id(audit_log_repo, test_user):
    """Test searching audit logs by entity ID."""
    task_id = uuid4()
    other_task_id = uuid4()

    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
    )
    log2 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskPuntedEvent",
        entity_id=task_id,
        entity_type="task",
    )
    log3 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=other_task_id,
        entity_type="task",
    )

    await audit_log_repo.put(log1)
    await audit_log_repo.put(log2)
    await audit_log_repo.put(log3)

    results = await audit_log_repo.search(AuditLogQuery(entity_id=task_id))

    assert len(results) == 2
    result_ids = [r.id for r in results]
    assert log1.id in result_ids
    assert log2.id in result_ids
    assert log3.id not in result_ids


@pytest.mark.asyncio
async def test_search_by_entity_type(audit_log_repo, test_user):
    """Test searching audit logs by entity type."""
    task_id = uuid4()
    message_id = uuid4()

    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
    )
    log2 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="MessageSentEvent",
        entity_id=message_id,
        entity_type="message",
    )

    await audit_log_repo.put(log1)
    await audit_log_repo.put(log2)

    results = await audit_log_repo.search(AuditLogQuery(entity_type="task"))

    assert len(results) == 1
    assert results[0].id == log1.id
    assert results[0].entity_type == "task"


@pytest.mark.asyncio
async def test_search_by_time_range(audit_log_repo, test_user):
    """Test searching audit logs by time range."""
    task_id1 = uuid4()
    task_id2 = uuid4()
    task_id3 = uuid4()

    base_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id1,
        entity_type="task",
        occurred_at=base_time - timedelta(hours=2),
    )
    log2 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id2,
        entity_type="task",
        occurred_at=base_time,
    )
    log3 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id3,
        entity_type="task",
        occurred_at=base_time + timedelta(hours=2),
    )

    await audit_log_repo.put(log1)
    await audit_log_repo.put(log2)
    await audit_log_repo.put(log3)

    # Search for logs in the middle hour
    results = await audit_log_repo.search(
        AuditLogQuery(
            occurred_after=base_time - timedelta(hours=1),
            occurred_before=base_time + timedelta(hours=1),
        )
    )

    assert len(results) == 1
    assert results[0].id == log2.id


@pytest.mark.asyncio
async def test_search_default_ordering(audit_log_repo, test_user):
    """Test that search defaults to ordering by occurred_at descending."""
    task_id1 = uuid4()
    task_id2 = uuid4()
    task_id3 = uuid4()

    base_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id1,
        entity_type="task",
        occurred_at=base_time,
    )
    log2 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id2,
        entity_type="task",
        occurred_at=base_time + timedelta(hours=1),
    )
    log3 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id3,
        entity_type="task",
        occurred_at=base_time - timedelta(hours=1),
    )

    # Insert out of order
    await audit_log_repo.put(log1)
    await audit_log_repo.put(log3)
    await audit_log_repo.put(log2)

    results = await audit_log_repo.search(AuditLogQuery())

    assert len(results) == 3
    # Should be ordered by occurred_at descending (most recent first)
    assert results[0].id == log2.id
    assert results[1].id == log1.id
    assert results[2].id == log3.id


@pytest.mark.asyncio
async def test_entity_to_row_and_back(audit_log_repo, test_user):
    """Test round-trip conversion: entity -> row -> entity."""
    task_id = uuid4()
    original = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
        meta={"key": "value", "nested": {"data": 123}},
    )

    # Convert to row
    row = audit_log_repo.entity_to_row(original)

    # Verify row structure
    assert row["id"] == original.id
    assert row["user_id"] == test_user.id
    assert row["activity_type"] == "TaskCompletedEvent"
    assert row["entity_id"] == task_id
    assert row["entity_type"] == "task"
    assert row["meta"] == original.meta

    # Convert back to entity
    restored = audit_log_repo.row_to_entity(row)

    # Verify entity matches original
    assert restored.id == original.id
    assert restored.user_id == original.user_id
    assert restored.activity_type == original.activity_type
    assert restored.entity_id == original.entity_id
    assert restored.entity_type == original.entity_type
    assert restored.meta == original.meta
    assert restored.occurred_at == original.occurred_at


@pytest.mark.asyncio
async def test_empty_meta_handling(audit_log_repo, test_user):
    """Test that empty meta is properly handled."""
    task_id = uuid4()
    audit_log = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
        meta={},
    )
    await audit_log_repo.put(audit_log)

    retrieved = await audit_log_repo.get(audit_log.id)
    assert retrieved.meta == {}


@pytest.mark.asyncio
async def test_user_scoping(audit_log_repo, test_user, create_test_user):
    """Test that audit logs are scoped to user."""
    other_user = await create_test_user()
    other_user_repo = AuditLogRepository(user_id=other_user.id)

    task_id = uuid4()
    log1 = AuditLogEntity(
        user_id=test_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
    )
    log2 = AuditLogEntity(
        user_id=other_user.id,
        activity_type="TaskCompletedEvent",
        entity_id=task_id,
        entity_type="task",
    )

    await audit_log_repo.put(log1)
    await other_user_repo.put(log2)

    # Each user should only see their own logs
    test_user_results = await audit_log_repo.search(AuditLogQuery())
    other_user_results = await other_user_repo.search(AuditLogQuery())

    assert len(test_user_results) == 1
    assert test_user_results[0].id == log1.id
    assert len(other_user_results) == 1
    assert other_user_results[0].id == log2.id


@pytest.mark.asyncio
async def test_paged_search(audit_log_repo, test_user):
    """Test paged search with limit and offset."""
    # Create multiple audit logs
    for _i in range(5):
        task_id = uuid4()
        log = AuditLogEntity(
            user_id=test_user.id,
            activity_type="TaskCompletedEvent",
            entity_id=task_id,
            entity_type="task",
        )
        await audit_log_repo.put(log)

    # Test pagination
    page1 = await audit_log_repo.paged_search(AuditLogQuery(limit=2, offset=0))
    page2 = await audit_log_repo.paged_search(AuditLogQuery(limit=2, offset=2))

    assert len(page1.items) == 2
    assert page1.total == 5
    assert page1.has_next is True
    assert page1.has_previous is False

    assert len(page2.items) == 2
    assert page2.total == 5
    assert page2.has_next is True
    assert page2.has_previous is True
