from lykke.domain.value_objects.activity_type import ActivityType


def test_activity_type_enum_values() -> None:
    assert ActivityType.TASK_COMPLETED.value == "TASK_COMPLETED"
    assert ActivityType.TASK_PUNTED.value == "TASK_PUNTED"
    assert ActivityType.MESSAGE_SENT.value == "MESSAGE_SENT"
    assert ActivityType.MESSAGE_RECEIVED.value == "MESSAGE_RECEIVED"
