"""Integration tests for automatic audit log creation from audited events."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, TaskEntity
from lykke.domain.events.task_events import TaskCompletedEvent, TaskStatusChangedEvent
from lykke.infrastructure.gateways import StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_task_completed_event_auto_creates_audit_log(
    test_user, day_template_repo, day_repo, task_repo, audit_log_repo
):
    """Test that TaskCompletedEvent automatically creates an audit log."""
    user_id = test_user.id
    task_date = dt_date(2025, 11, 27)

    # Create day template
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )
    await day_template_repo.put(template)

    # Create day
    day = DayEntity.create_for_date(task_date, user_id, template)
    await day_repo.put(day)

    # Create task
    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    await task_repo.put(task)

    # Record complete action which should emit TaskCompletedEvent
    action = value_objects.Action(type=value_objects.ActionType.COMPLETE)
    updated_task = day.record_task_action(task, action)

    # Commit via UOW - audit log should be auto-created
    uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())
    async with uow:
        uow.add(day)
        uow.add(updated_task)

    # Verify audit log was automatically created
    audit_logs = await audit_log_repo.search(value_objects.AuditLogQuery())
    assert len(audit_logs) == 1
    audit_log = audit_logs[0]
    assert audit_log.activity_type == value_objects.ActivityType.TASK_COMPLETED
    assert audit_log.entity_id == task.id
    assert audit_log.entity_type == "task"
    assert audit_log.user_id == user_id
    assert "completed_at" in audit_log.meta


@pytest.mark.asyncio
async def test_task_punt_event_auto_creates_audit_log(
    test_user, day_template_repo, day_repo, task_repo, audit_log_repo
):
    """Test that TaskPuntedEvent automatically creates an audit log."""
    user_id = test_user.id
    task_date = dt_date(2025, 11, 27)

    # Create day template
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )
    await day_template_repo.put(template)

    # Create day
    day = DayEntity.create_for_date(task_date, user_id, template)
    await day_repo.put(day)

    # Create task
    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    await task_repo.put(task)

    # Record punt action which should emit TaskPuntedEvent
    action = value_objects.Action(type=value_objects.ActionType.PUNT)
    updated_task = day.record_task_action(task, action)

    # Commit via UOW - audit log should be auto-created
    uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())
    async with uow:
        uow.add(day)
        uow.add(updated_task)

    # Verify audit log was automatically created
    audit_logs = await audit_log_repo.search(value_objects.AuditLogQuery())
    assert len(audit_logs) == 1
    audit_log = audit_logs[0]
    assert audit_log.activity_type == value_objects.ActivityType.TASK_PUNTED
    assert audit_log.entity_id == task.id
    assert audit_log.entity_type == "task"
    assert audit_log.user_id == user_id
    assert audit_log.meta["old_status"] == value_objects.TaskStatus.READY.value
    assert audit_log.meta["new_status"] == value_objects.TaskStatus.PUNT.value


@pytest.mark.asyncio
async def test_audit_log_entity_does_not_trigger_more_audit_logs(
    test_user, audit_log_repo
):
    """Test that AuditLogEntity itself does not trigger infinite audit log creation."""
    user_id = test_user.id

    from lykke.domain.entities import AuditLogEntity

    # Create an audit log entity directly
    audit_log = AuditLogEntity(
        user_id=user_id,
        activity_type=value_objects.ActivityType.TASK_COMPLETED,
        entity_id=uuid4(),
        entity_type="task",
    )

    # Commit via UOW - should not create additional audit logs
    uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())
    async with uow:
        await uow.create(audit_log)

    # Verify only one audit log exists (the one we created)
    audit_logs = await audit_log_repo.search(value_objects.AuditLogQuery())
    assert len(audit_logs) == 1
    assert audit_logs[0].id == audit_log.id
