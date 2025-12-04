from pydantic import BaseModel, Field

from planned import settings


class UserSettings(BaseModel):
    template_defaults: list[str] = Field(
        default_factory=lambda: ["default"] * 7,
    )


with open(f"{settings.DATA_PATH}/config/user-settings.json") as f:
    user_settings: UserSettings = UserSettings.model_validate_json(
        f.read(),
        by_alias=False,
        by_name=True,
    )
