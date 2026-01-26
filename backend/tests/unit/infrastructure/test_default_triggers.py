from lykke.infrastructure.data.default_triggers import DEFAULT_TRIGGERS


def test_default_triggers_structure() -> None:
    assert len(DEFAULT_TRIGGERS) > 0

    first = DEFAULT_TRIGGERS[0]
    assert set(first.keys()) == {"name", "description"}
    assert isinstance(first["name"], str)
    assert isinstance(first["description"], str)

    assert all({"name", "description"} == set(entry.keys()) for entry in DEFAULT_TRIGGERS)
