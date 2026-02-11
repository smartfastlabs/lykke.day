"""Unit tests for RoutineDefinitionEntity."""

from __future__ import annotations

from datetime import time
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.events.routine_definition import RoutineDefinitionUpdatedEvent


def _build_routine_definition() -> RoutineDefinitionEntity:
    return RoutineDefinitionEntity(
        user_id=uuid4(),
        name="Morning routine",
        category=value_objects.TaskCategory.WORK,
        routine_definition_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY
        ),
    )


def _build_task() -> value_objects.RoutineDefinitionTask:
    return value_objects.RoutineDefinitionTask(
        task_definition_id=uuid4(),
        name="Stretch",
        task_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY
        ),
    )


def test_add_task_emits_event() -> None:
    routine = _build_routine_definition()
    task = _build_task()

    updated = routine.add_task(task)

    assert updated.tasks == [task]
    event = updated.collect_events()[0]
    assert isinstance(event, RoutineDefinitionUpdatedEvent)
    assert event.update_object.tasks == [task]


def test_update_task_updates_fields_and_emits_event() -> None:
    routine = _build_routine_definition()
    task = _build_task()
    extra_task = value_objects.RoutineDefinitionTask(
        task_definition_id=uuid4(),
        name="Extra",
        task_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.WEEKLY
        ),
    )
    routine = routine.add_task(task)
    routine = routine.add_task(extra_task)
    routine.collect_events()

    update = value_objects.RoutineDefinitionTask(
        id=task.id,
        task_definition_id=task.task_definition_id,
        name="Stretch and breathe",
        task_schedule=None,
        time_window=value_objects.TimeWindow(
            start_time=time(9, 0)
        ),
    )

    updated = routine.update_task(update)

    assert updated.tasks[0].name == "Stretch and breathe"
    assert updated.tasks[1] == extra_task
    event = updated.collect_events()[0]
    assert isinstance(event, RoutineDefinitionUpdatedEvent)
    assert event.update_object.tasks == updated.tasks


def test_update_task_raises_when_missing() -> None:
    routine = _build_routine_definition()

    update = value_objects.RoutineDefinitionTask(
        id=uuid4(),
        task_definition_id=uuid4(),
        name="Missing",
    )

    with pytest.raises(NotFoundError, match="Routine task not found"):
        routine.update_task(update)


def test_remove_task_emits_event() -> None:
    routine = _build_routine_definition()
    task = _build_task()
    routine = routine.add_task(task)
    routine.collect_events()

    updated = routine.remove_task(task.id)

    assert updated.tasks == []
    event = updated.collect_events()[0]
    assert isinstance(event, RoutineDefinitionUpdatedEvent)
    assert event.update_object.tasks == []


def test_remove_task_raises_when_missing() -> None:
    routine = _build_routine_definition()

    with pytest.raises(NotFoundError, match="Routine task not found"):
        routine.remove_task(uuid4())
