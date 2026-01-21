"""Unit tests for presentation layer mappers."""

from lykke.presentation.api.schemas.mappers import map_user_to_schema
from lykke.presentation.api.schemas.user import UserSettingsSchema
from lykke.domain.value_objects import UserSetting
from lykke.domain.entities import UserEntity


def test_map_user_to_schema_accepts_user_setting_dataclass() -> None:
    """Ensure map_user_to_schema works with the expected UserSetting dataclass."""
    settings = UserSetting(template_defaults=["a", "b", "c", "d", "e", "f", "g"])
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=settings,
    )

    schema = map_user_to_schema(user)

    assert schema.settings.template_defaults == ["a", "b", "c", "d", "e", "f", "g"]
    assert schema.email == "test@example.com"

