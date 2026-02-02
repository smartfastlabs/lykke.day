from lykke.domain import value_objects
from lykke.infrastructure.unit_of_work import _build_update_patch


def test_build_update_patch_from_update_object() -> None:
    update = value_objects.TaskUpdateObject(status=value_objects.TaskStatus.COMPLETE)

    patch = _build_update_patch(update)

    assert patch == [
        {"op": "replace", "path": "/status", "value": "COMPLETE"}
    ]
