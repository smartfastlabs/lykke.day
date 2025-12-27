from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    template_defaults: list[str] = Field(
        default_factory=lambda: ["default"] * 7,
    )
