"""Unit tests for AuditLog entity."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.exceptions import DomainError
from lykke.domain.entities import AuditLogEntity
from lykke.domain.value_objects.activity_type import ActivityType


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return uuid4()


@pytest.fixture
def test_task_id():
    """Test task ID."""
    return uuid4()


def test_create_task_completed(test_user_id, test_task_id):
    """Test create_task_completed factory method."""
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
        meta={"key": "value"},
    )

    assert audit_log.user_id == test_user_id
    assert audit_log.activity_type == ActivityType.TASK_COMPLETED
    assert audit_log.entity_id == test_task_id
    assert audit_log.entity_type == "task"
    assert audit_log.meta == {"key": "value"}
    assert audit_log.occurred_at is not None


def test_create_task_completed_default_meta(test_user_id, test_task_id):
    """Test create_task_completed with default empty meta."""
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
    )

    assert audit_log.meta == {}


def test_create_task_punted(test_user_id, test_task_id):
    """Test create_task_punted factory method."""
    audit_log = AuditLogEntity.create_task_punted(
        user_id=test_user_id,
        task_id=test_task_id,
        meta={"reason": "not ready"},
    )

    assert audit_log.user_id == test_user_id
    assert audit_log.activity_type == ActivityType.TASK_PUNTED
    assert audit_log.entity_id == test_task_id
    assert audit_log.entity_type == "task"
    assert audit_log.meta == {"reason": "not ready"}


def test_create_task_punted_default_meta(test_user_id, test_task_id):
    """Test create_task_punted with default empty meta."""
    audit_log = AuditLogEntity.create_task_punted(
        user_id=test_user_id,
        task_id=test_task_id,
    )

    assert audit_log.meta == {}


def test_delete_raises_error(test_user_id, test_task_id):
    """Test that delete() raises DomainError."""
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
    )

    with pytest.raises(DomainError, match="cannot be deleted"):
        audit_log.delete()


def test_apply_update_raises_error(test_user_id, test_task_id):
    """Test that apply_update() raises DomainError."""
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
    )

    # Create a dummy update object
    class DummyUpdate:
        pass

    class DummyEvent:
        pass

    with pytest.raises(DomainError, match="cannot be updated"):
        audit_log.apply_update(DummyUpdate(), DummyEvent)


def test_audit_log_immutability(test_user_id, test_task_id):
    """Test that audit log is immutable - cannot be modified after creation."""
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
        meta={"original": "value"},
    )

    # Verify we can't delete
    with pytest.raises(DomainError):
        audit_log.delete()

    # Verify we can't update
    with pytest.raises(DomainError):
        audit_log.apply_update(None, None)


def test_audit_log_occurred_at_auto_set(test_user_id, test_task_id):
    """Test that occurred_at is automatically set to current time."""
    before = datetime.now(UTC)
    audit_log = AuditLogEntity.create_task_completed(
        user_id=test_user_id,
        task_id=test_task_id,
    )
    after = datetime.now(UTC)

    assert before <= audit_log.occurred_at <= after


def test_audit_log_custom_occurred_at(test_user_id, test_task_id):
    """Test that occurred_at can be explicitly set."""
    custom_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
    audit_log = AuditLogEntity(
        user_id=test_user_id,
        activity_type=ActivityType.TASK_COMPLETED,
        entity_id=test_task_id,
        entity_type="task",
        occurred_at=custom_time,
    )

    assert audit_log.occurred_at == custom_time
