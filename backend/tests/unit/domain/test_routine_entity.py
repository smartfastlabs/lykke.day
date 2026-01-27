"""Unit tests for RoutineEntity."""

from __future__ import annotations

from datetime import date as dt_date
from uuid import uuid4

from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity, RoutineEntity


def test_routine_from_definition_copies_fields() -> None:
    user_id = uuid4()
    routine_definition = RoutineDefinitionEntity(
        user_id=user_id,
        name="Morning routine",
        category=value_objects.TaskCategory.WORK,
        routine_definition_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY
        ),
        description="Start the day",
    )

    routine = RoutineEntity.from_definition(
        routine_definition=routine_definition,
        date=dt_date(2025, 11, 27),
        user_id=user_id,
    )

    assert routine.name == routine_definition.name
    assert routine.description == routine_definition.description
    assert routine.routine_definition_id == routine_definition.id
