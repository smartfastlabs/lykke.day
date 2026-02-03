"""Unit tests for RecordTaskActionHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.task import (
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    TaskEntity,
    UserEntity,
)
from lykke.domain.events.task_events import (
    TaskActionRecordedEvent,
    TaskStateUpdatedEvent,
)
from tests.support.dobles import (
    create_day_repo_double,
    create_day_template_repo_double,
    create_read_only_repos_double,
    create_task_repo_double,
    create_uow_double,
    create_uow_factory_double,
    create_user_repo_double,
)


@pytest.mark.asyncio
async def test_record_task_action_adds_task_and_day_to_uow():
    """Verify task and day are added to UoW after recording action."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    # Create test data
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

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

    # Setup repositories
    task_repo = create_task_repo_double()
    allow(task_repo).get.with_args(task.id).and_return(task)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = RecordTaskActionHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    # Create action
    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act
    result = await handler.handle(
        RecordTaskActionCommand(task_id=task.id, action=action)
    )

    # Assert
    assert result.status == value_objects.TaskStatus.COMPLETE
    assert len(result.actions) == 1
    assert result.actions[0].type == value_objects.ActionType.COMPLETE

    # Verify both day and task were added to UoW
    assert len(uow.added) == 2
    added_entities = uow.added
    assert any(isinstance(e, DayEntity) for e in added_entities)
    assert any(isinstance(e, TaskEntity) for e in added_entities)

    # Verify audit logs are no longer manually created
    # (They are now automatically created by the UOW when processing entities with audited events)
    assert len(uow.created) == 0


@pytest.mark.asyncio
async def test_record_task_action_raises_domain_events():
    """Verify domain events are raised when recording action."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

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

    task_repo = create_task_repo_double()
    allow(task_repo).get.with_args(task.id).and_return(task)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = RecordTaskActionHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act
    result = await handler.handle(
        RecordTaskActionCommand(task_id=task.id, action=action)
    )

    # Assert - check that task has domain events
    task_events = [
        e for e in result._domain_events if isinstance(e, TaskStateUpdatedEvent)
    ]
    assert len(task_events) > 0

    # Check day has domain events
    day_from_uow = next(e for e in uow.added if isinstance(e, DayEntity))
    day_events = [
        e for e in day_from_uow._domain_events if isinstance(e, TaskActionRecordedEvent)
    ]
    assert len(day_events) > 0


@pytest.mark.asyncio
async def test_record_task_action_raises_if_day_missing():
    """Verify error is raised if day doesn't exist when recording action."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

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

    task_repo = create_task_repo_double()
    allow(task_repo).get.with_args(task.id).and_return(task)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = RecordTaskActionHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
    )

    # Act / Assert
    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(RecordTaskActionCommand(task_id=task.id, action=action))


@pytest.mark.asyncio
async def test_record_task_action_punt_updates_status():
    """Verify punting a task updates its status correctly."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)

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

    task_repo = create_task_repo_double()
    allow(task_repo).get.with_args(task.id).and_return(task)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.with_args(user_id).and_return(user)

    ro_repos = create_read_only_repos_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        task_repo=task_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = RecordTaskActionHandler(
        ro_repos,
        uow_factory,
        UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
    )

    action = value_objects.Action(
        type=value_objects.ActionType.PUNT,
    )

    # Act
    result = await handler.handle(
        RecordTaskActionCommand(task_id=task.id, action=action)
    )

    # Assert
    assert result.status == value_objects.TaskStatus.PUNT
    assert len(result.actions) == 1
    assert result.actions[0].type == value_objects.ActionType.PUNT
    assert result.completed_at is None  # Punt doesn't set completed_at

    # Verify audit logs are no longer manually created
    # (They are now automatically created by the UOW when processing entities with audited events)
    assert len(uow.created) == 0
