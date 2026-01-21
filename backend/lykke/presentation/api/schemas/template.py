"""Template schemas."""

from uuid import UUID

from .base import BaseEntitySchema, BaseSchema


class SystemTemplatePartSchema(BaseSchema):
    """System template part from file system."""

    part: str
    content: str
    has_user_override: bool


class SystemTemplateSchema(BaseSchema):
    """System template from file system."""

    usecase: str
    name: str
    parts: list[SystemTemplatePartSchema]
    has_user_override: bool


class TemplateSchema(BaseEntitySchema):
    """User override template."""

    user_id: UUID
    usecase: str
    key: str
    name: str
    description: str | None
    content: str


class TemplatePartDetailSchema(BaseSchema):
    """System template part + user override."""

    part: str
    system_content: str
    override: TemplateSchema | None = None


class TemplateDetailSchema(BaseSchema):
    """Combined system templates + user overrides."""

    usecase: str
    name: str
    parts: list[TemplatePartDetailSchema]


class TemplateCreateSchema(BaseSchema):
    """API schema for creating a template override."""

    usecase: str
    key: str
    name: str | None = None
    description: str | None = None
    content: str


class TemplateUpdateSchema(BaseSchema):
    """API schema for updating a template override."""

    name: str | None = None
    description: str | None = None
    content: str | None = None


class TemplatePreviewSchema(BaseSchema):
    """Preview for rendered template output."""

    system_prompt: str
    context_prompt: str
    ask_prompt: str
    context_data: dict


class TemplatePreviewRequestSchema(BaseSchema):
    """Request body for previewing templates."""

    usecase: str
