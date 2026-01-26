from lykke.infrastructure.data.default_tactics import DEFAULT_TACTICS


def test_default_tactics_structure() -> None:
    assert len(DEFAULT_TACTICS) > 0

    first = DEFAULT_TACTICS[0]
    assert set(first.keys()) == {"name", "description"}
    assert isinstance(first["name"], str)
    assert isinstance(first["description"], str)

    assert all({"name", "description"} == set(entry.keys()) for entry in DEFAULT_TACTICS)
