"""Unit tests for routine-wide task actions."""

from datetime import UTC, date as dt_date, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.task import (
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    RoutineEntity,
    TaskEntity,
    UserEntity,
)
from tests.support.dobles import (
    create_day_repo_double,
    create_read_only_repos_double,
    create_routine_repo_double,
    create_task_repo_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


def _make_day(user_id: object, task_date: dt_date) -> DayEntity:
    template = DayTemplateEntity(
        user_id=user_id,  # type: ignore[arg-type]
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(task_date, user_id, template)  # type: ignore[arg-type]


def _make_tasks(
    *,
    user_id: object,
    task_date: dt_date,
    routine_definition_id: object,
) -> tuple[TaskEntity, TaskEntity, TaskEntity, datetime]:
    ready_task = TaskEntity(
        id=uuid4(),
        user_id=user_id,  # type: ignore[arg-type]
        scheduled_date=task_date,
        name="Ready task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
        routine_definition_id=routine_definition_id,  # type: ignore[arg-type]
    )
    punted_task = TaskEntity(
        id=uuid4(),
        user_id=user_id,  # type: ignore[arg-type]
        scheduled_date=task_date,
        name="Already punted",
        status=value_objects.TaskStatus.PUNT,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
        routine_definition_id=routine_definition_id,  # type: ignore[arg-type]
    )
    completed_at = datetime(2025, 11, 27, 12, 0, tzinfo=UTC)
    completed_task = TaskEntity(
        id=uuid4(),
        user_id=user_id,  # type: ignore[arg-type]
        scheduled_date=task_date,
        name="Already complete",
        status=value_objects.TaskStatus.COMPLETE,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
        completed_at=completed_at,
        routine_definition_id=routine_definition_id,  # type: ignore[arg-type]
    )
    return ready_task, punted_task, completed_task, completed_at


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action_type", "expected_ready_status"),
    [
        (value_objects.ActionType.PUNT, value_objects.TaskStatus.PUNT),
        (value_objects.ActionType.COMPLETE, value_objects.TaskStatus.COMPLETE),
    ],
)
async def test_record_routine_action_only_updates_tasks_not_punted_or_completed(
    action_type: value_objects.ActionType,
    expected_ready_status: value_objects.TaskStatus,
) -> None:
    """RecordRoutineActionHandler should skip tasks already punted/completed."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)
    routine_definition_id = uuid4()

    day = _make_day(user_id, task_date)

    routine = RoutineEntity(
        user_id=user_id,
        date=task_date,
        routine_definition_id=routine_definition_id,
        name="Morning routine",
        category=value_objects.TaskCategory.WORK,
        status=value_objects.TaskStatus.NOT_STARTED,
    )

    ready_task, punted_task, completed_task, completed_at = _make_tasks(
        user_id=user_id,
        task_date=task_date,
        routine_definition_id=routine_definition_id,
    )

    task_repo = create_task_repo_double()
    allow(task_repo).search.and_return([ready_task, punted_task, completed_task])

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(task_date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    routine_repo = create_routine_repo_double()
    allow(routine_repo).get.with_args(routine.id).and_return(routine)

    ro_repos = create_read_only_repos_double(
        task_repo=task_repo,
        day_repo=day_repo,
        routine_repo=routine_repo,
    )
    uow = create_uow_double(
        task_repo=task_repo,
        day_repo=day_repo,
        routine_repo=routine_repo,
    )
    uow_factory = create_uow_factory_double(uow)

    action = value_objects.Action(type=action_type)

    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    routine_handler = RecordRoutineActionHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    result = await routine_handler.handle(
        RecordRoutineActionCommand(routine_id=routine.id, action=action)
    )

    # Assert: only READY task changed + returned
    assert len(result) == 1
    assert result[0].id == ready_task.id
    assert ready_task.status == expected_ready_status
    assert len(ready_task.actions) == 1
    assert ready_task.actions[0].type == action_type

    # Skipped tasks are untouched
    assert punted_task.status == value_objects.TaskStatus.PUNT
    assert punted_task.actions == []
    assert completed_task.status == value_objects.TaskStatus.COMPLETE
    assert completed_task.actions == []
    assert completed_task.completed_at == completed_at

    # Day is always added; only the eligible task should be added (skipped tasks unchanged)
    assert len(uow.added) == 2
    assert any(isinstance(e, DayEntity) for e in uow.added)
    assert any(isinstance(e, TaskEntity) and e.id == ready_task.id for e in uow.added)
