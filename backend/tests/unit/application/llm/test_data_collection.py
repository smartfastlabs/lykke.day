"""Unit tests for generic data collection helpers."""

from datetime import time

from lykke.application.llm.data_collection import (
    DataCollectionField,
    DataCollectionSchema,
    DataCollectionState,
    DataclassCoercer,
)
from lykke.domain import value_objects


def test_data_collection_state_missing_required_fields() -> None:
    schema = DataCollectionSchema(
        dataclass_type=value_objects.OnboardingProfile,
        fields=[
            DataCollectionField(name="timezone", required=True),
            DataCollectionField(name="preferred_name", required=True),
        ],
    )
    state = DataCollectionState()
    assert state.missing_required_fields(schema) == ["preferred_name", "timezone"]

    state = state.merge_collected({"timezone": "America/Chicago"})
    assert state.missing_required_fields(schema) == ["preferred_name"]


def test_dataclass_coercer_coerces_time_and_nested_value_object() -> None:
    coerced = DataclassCoercer.coerce_partial(
        dataclass_type=value_objects.OnboardingProfile,
        raw={
            "preferred_name": " Todd ",
            "timezone": "America/Chicago",
            "morning_overview_time": "08:30",
            "goals": ["sleep", 123],
            "work_hours": {
                "start_time": "09:00",
                "end_time": "17:00",
                "weekdays": [0, "4"],
            },
        },
    )

    assert coerced["preferred_name"] == "Todd"
    assert coerced["timezone"] == "America/Chicago"
    assert coerced["morning_overview_time"] == time(8, 30)
    assert coerced["goals"] == ["sleep", "123"]

    wh = coerced["work_hours"]
    assert isinstance(wh, value_objects.WorkHours)
    assert wh.start_time == time(9, 0)
    assert wh.weekdays == [value_objects.DayOfWeek.MONDAY, value_objects.DayOfWeek.FRIDAY]

