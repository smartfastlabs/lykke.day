from datetime import UTC, date, datetime, time
from uuid import uuid4

from lykke.domain.entities import RoutineEntity, TaskEntity
from lykke.domain.services.timing_status import TimingStatusService
from lykke.domain.value_objects import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
    TimeWindow,
    TimingStatus,
)


def _build_task(*, scheduled_date: date, time_window: TimeWindow) -> TaskEntity:
    return TaskEntity(
        user_id=uuid4(),
        scheduled_date=scheduled_date,
        name="Test Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.WORK,
        category=TaskCategory.WORK,
        frequency=TaskFrequency.ONCE,
        time_window=time_window,
    )


def test_task_timing_status_inactive_before_start() -> None:
    now = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    task = _build_task(
        scheduled_date=now.date(),
        time_window=TimeWindow(start_time=time(10, 0), end_time=time(11, 0)),
    )

    result = TimingStatusService.task_status(task, now, timezone="UTC")

    assert result.status == TimingStatus.HIDDEN
    assert result.next_available_time == datetime(2025, 1, 1, 10, 0, tzinfo=UTC)


def test_task_timing_status_active_during_window() -> None:
    now = datetime(2025, 1, 1, 10, 30, tzinfo=UTC)
    task = _build_task(
        scheduled_date=now.date(),
        time_window=TimeWindow(start_time=time(10, 0), end_time=time(11, 0)),
    )

    result = TimingStatusService.task_status(task, now, timezone="UTC")

    assert result.status == TimingStatus.ACTIVE
    assert result.next_available_time is None


def test_task_timing_status_past_due_after_deadline() -> None:
    now = datetime(2025, 1, 1, 10, 30, tzinfo=UTC)
    task = _build_task(
        scheduled_date=now.date(),
        time_window=TimeWindow(end_time=time(10, 0)),
    )

    result = TimingStatusService.task_status(task, now, timezone="UTC")

    assert result.status == TimingStatus.PAST_DUE


def test_routine_timing_status_inactive_when_task_upcoming() -> None:
    now = datetime(2025, 1, 1, 9, 40, tzinfo=UTC)
    routine_definition_id = uuid4()
    routine = RoutineEntity(
        user_id=uuid4(),
        date=now.date(),
        routine_definition_id=routine_definition_id,
        name="Morning",
        category=TaskCategory.WORK,
        description="Routine",
    )
    task = _build_task(
        scheduled_date=now.date(),
        time_window=TimeWindow(start_time=time(10, 0)),
    )
    task.routine_definition_id = routine_definition_id

    result = TimingStatusService.routine_status(routine, [task], now, timezone="UTC")

    assert result.status == TimingStatus.INACTIVE
