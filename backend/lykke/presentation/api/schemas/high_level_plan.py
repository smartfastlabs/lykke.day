"""High level plan schema."""

from pydantic import Field

from .base import BaseSchema


class HighLevelPlanSchema(BaseSchema):
    """API schema for high level plan value object."""

    title: str | None = None
    text: str | None = None
    intentions: list[str] = Field(default_factory=list)
