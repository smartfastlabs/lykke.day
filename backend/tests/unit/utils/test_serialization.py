from dataclasses import dataclass
from uuid import UUID, uuid4

from lykke.core.utils.serialization import dataclass_to_json_dict


@dataclass
class SampleItem:
    id: UUID
    name: str


def test_dataclass_to_json_dict_serializes_list_of_dataclasses() -> None:
    items = [
        SampleItem(id=uuid4(), name="first"),
        SampleItem(id=uuid4(), name="second"),
    ]

    serialized = dataclass_to_json_dict(items)

    assert isinstance(serialized, list)
    assert serialized[0]["id"] == str(items[0].id)
    assert serialized[0]["name"] == "first"
    assert serialized[1]["id"] == str(items[1].id)
    assert serialized[1]["name"] == "second"
