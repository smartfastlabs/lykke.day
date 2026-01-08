"""Unit tests for presentation layer mappers."""

from lykke.presentation.api.schemas.mappers import map_user_to_schema
from lykke.presentation.api.schemas.user import UserSettingsSchema
from lykke.domain.entities import UserEntity


def test_map_user_to_schema_handles_non_dataclass_settings() -> None:
    """
    Ensure map_user_to_schema works when settings is a pydantic model (not a dataclass).

    The original bug called `asdict` unconditionally and failed with:
    TypeError: asdict() should be called on dataclass instances
    """
    settings = UserSettingsSchema(template_defaults=["a", "b", "c", "d", "e", "f", "g"])
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=settings,  # pydantic model, not dataclass
    )

    schema = map_user_to_schema(user)

    assert schema.settings.template_defaults == ["a", "b", "c", "d", "e", "f", "g"]
    assert schema.email == "test@example.com"

