from lykke.domain import value_objects
from lykke.infrastructure.data.default_task_definitions import DEFAULT_TASK_DEFINITIONS


def test_default_task_definitions_structure() -> None:
    assert len(DEFAULT_TASK_DEFINITIONS) > 0

    first = DEFAULT_TASK_DEFINITIONS[0]
    assert set(first.keys()) == {"name", "description", "type"}
    assert isinstance(first["name"], str)
    assert isinstance(first["description"], str)
    assert isinstance(first["type"], value_objects.TaskType)

    assert all(
        {
            "name",
            "description",
            "type",
        }
        == set(entry.keys())
        for entry in DEFAULT_TASK_DEFINITIONS
    )
