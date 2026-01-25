"""Map RoutineDefinition API schemas to domain value objects."""

from uuid import UUID

from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects import RoutineDefinitionUpdateObject
from lykke.domain.value_objects.routine_definition import (
    RecurrenceSchedule,
    RoutineDefinitionTask,
    TimeWindow,
)
from lykke.domain.value_objects.task import TaskSchedule
from lykke.presentation.api.schemas.routine_definition import (
    RecurrenceScheduleSchema,
    RoutineDefinitionCreateSchema,
    RoutineDefinitionTaskCreateSchema,
    RoutineDefinitionTaskSchema,
    RoutineDefinitionTaskUpdateSchema,
    RoutineDefinitionUpdateSchema,
    TimeWindowSchema,
)
from lykke.presentation.api.schemas.task import TaskScheduleSchema


def _schema_to_recurrence_schedule(
    s: RecurrenceScheduleSchema | None,
) -> RecurrenceSchedule | None:
    if s is None:
        return None
    return RecurrenceSchedule(
        frequency=s.frequency,
        weekdays=s.weekdays,
        day_number=s.day_number,
    )


def _schema_to_time_window(s: TimeWindowSchema | None) -> TimeWindow | None:
    if s is None:
        return None
    return TimeWindow(
        available_time=s.available_time,
        start_time=s.start_time,
        end_time=s.end_time,
        cutoff_time=s.cutoff_time,
    )


def _schema_to_task_schedule(s: TaskScheduleSchema | None) -> TaskSchedule | None:
    if s is None:
        return None
    return TaskSchedule(
        available_time=s.available_time,
        start_time=s.start_time,
        end_time=s.end_time,
        timing_type=s.timing_type,
    )


def _task_schema_to_vo(
    s: RoutineDefinitionTaskSchema,
    *,
    include_id: bool,
) -> RoutineDefinitionTask:
    schedule = _schema_to_task_schedule(s.schedule)
    task_schedule = _schema_to_recurrence_schedule(s.task_schedule)
    time_window = _schema_to_time_window(s.time_window)
    if include_id and s.id is not None:
        return RoutineDefinitionTask(
            id=s.id,
            task_definition_id=s.task_definition_id,
            name=s.name,
            schedule=schedule,
            task_schedule=task_schedule,
            time_window=time_window,
        )
    return RoutineDefinitionTask(
        task_definition_id=s.task_definition_id,
        name=s.name,
        schedule=schedule,
        task_schedule=task_schedule,
        time_window=time_window,
    )


def task_create_schema_to_vo(s: RoutineDefinitionTaskCreateSchema) -> RoutineDefinitionTask:
    schedule = _schema_to_task_schedule(s.schedule)
    task_schedule = _schema_to_recurrence_schedule(s.task_schedule)
    time_window = _schema_to_time_window(s.time_window)
    return RoutineDefinitionTask(
        task_definition_id=s.task_definition_id,
        name=s.name,
        schedule=schedule,
        task_schedule=task_schedule,
        time_window=time_window,
    )


def task_update_schema_to_partial_vo(
    s: RoutineDefinitionTaskUpdateSchema,
    task_id: UUID,
) -> RoutineDefinitionTask:
    """Build partial RoutineDefinitionTask for update; task_definition_id is preserved by handler."""
    schedule = _schema_to_task_schedule(s.schedule)
    task_schedule = _schema_to_recurrence_schedule(s.task_schedule)
    time_window = _schema_to_time_window(s.time_window)
    return RoutineDefinitionTask(
        id=task_id,
        task_definition_id=UUID("00000000-0000-0000-0000-000000000000"),
        name=s.name,
        schedule=schedule,
        task_schedule=task_schedule,
        time_window=time_window,
    )


def create_schema_to_entity(
    data: RoutineDefinitionCreateSchema,
    user_id: UUID,
) -> RoutineDefinitionEntity:
    """Convert RoutineDefinitionCreateSchema to RoutineDefinitionEntity."""
    schedule = _schema_to_recurrence_schedule(data.routine_definition_schedule)
    assert schedule is not None  # required by create schema
    time_window = _schema_to_time_window(data.time_window)
    tasks = [_task_schema_to_vo(t, include_id=True) for t in (data.tasks or [])]
    return RoutineDefinitionEntity(
        user_id=user_id,
        name=data.name,
        category=data.category,
        routine_definition_schedule=schedule,
        description=data.description,
        time_window=time_window,
        tasks=tasks,
    )


def update_schema_to_update_object(
    data: RoutineDefinitionUpdateSchema,
) -> RoutineDefinitionUpdateObject:
    """Convert RoutineDefinitionUpdateSchema to RoutineDefinitionUpdateObject."""
    schedule = _schema_to_recurrence_schedule(data.routine_definition_schedule)
    time_window = _schema_to_time_window(data.time_window)
    tasks: list[RoutineDefinitionTask] | None = None
    if data.tasks is not None:
        tasks = [_task_schema_to_vo(t, include_id=True) for t in data.tasks]
    return RoutineDefinitionUpdateObject(
        name=data.name,
        category=data.category,
        routine_definition_schedule=schedule,
        description=data.description,
        time_window=time_window,
        tasks=tasks,
    )
