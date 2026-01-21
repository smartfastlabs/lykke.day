"""Router for template overrides and previews."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from lykke.application.commands.template import (
    CreateTemplateCommand,
    CreateTemplateHandler,
    DeleteTemplateCommand,
    DeleteTemplateHandler,
    UpdateTemplateCommand,
    UpdateTemplateHandler,
)
from lykke.application.queries.template import (
    ListSystemTemplatesHandler,
    ListSystemTemplatesQuery,
    ListTemplatesHandler,
    ListTemplatesQuery,
    PreviewTemplateHandler,
    PreviewTemplateQuery,
)
from lykke.core.utils.templates import template_display_name
from lykke.domain.entities import TemplateEntity, UserEntity
from lykke.domain.value_objects import TemplateUpdateObject
from lykke.presentation.api.schemas import (
    SystemTemplateSchema,
    SystemTemplatePartSchema,
    TemplateCreateSchema,
    TemplateDetailSchema,
    TemplatePartDetailSchema,
    TemplatePreviewRequestSchema,
    TemplatePreviewSchema,
    TemplateSchema,
    TemplateUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_template_to_schema

from .dependencies.factories import get_command_handler, get_query_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/templates/system", response_model=list[SystemTemplateSchema])
async def list_system_templates(
    list_system_templates_handler: Annotated[
        ListSystemTemplatesHandler, Depends(get_query_handler(ListSystemTemplatesHandler))
    ],
    list_templates_handler: Annotated[
        ListTemplatesHandler, Depends(get_query_handler(ListTemplatesHandler))
    ],
) -> list[SystemTemplateSchema]:
    """List system templates with override indicators."""
    system_templates = await list_system_templates_handler.handle(
        ListSystemTemplatesQuery()
    )
    overrides = await list_templates_handler.handle(ListTemplatesQuery())
    override_keys = {(template.usecase, template.key) for template in overrides}

    return [
        SystemTemplateSchema(
            usecase=template.usecase,
            name=template.name,
            parts=[
                SystemTemplatePartSchema(
                    part=part.part,
                    content=part.content,
                    has_user_override=(template.usecase, part.part) in override_keys,
                )
                for part in template.parts
            ],
            has_user_override=any(
                (template.usecase, part.part) in override_keys
                for part in template.parts
            ),
        )
        for template in system_templates
    ]


@router.get("/templates/overrides", response_model=list[TemplateSchema])
async def list_template_overrides(
    list_templates_handler: Annotated[
        ListTemplatesHandler, Depends(get_query_handler(ListTemplatesHandler))
    ],
) -> list[TemplateSchema]:
    """List template overrides for the current user."""
    templates = await list_templates_handler.handle(ListTemplatesQuery())
    return [map_template_to_schema(template) for template in templates]


@router.get("/templates/{usecase:path}", response_model=TemplateDetailSchema)
async def get_template_detail(
    usecase: str,
    list_system_templates_handler: Annotated[
        ListSystemTemplatesHandler, Depends(get_query_handler(ListSystemTemplatesHandler))
    ],
    list_templates_handler: Annotated[
        ListTemplatesHandler, Depends(get_query_handler(ListTemplatesHandler))
    ],
) -> TemplateDetailSchema:
    """Get system template with optional user override."""
    normalized_usecase = usecase.strip().strip("/")
    system_templates = await list_system_templates_handler.handle(
        ListSystemTemplatesQuery()
    )
    system_template = next(
        (
            template
            for template in system_templates
            if template.usecase == normalized_usecase
        ),
        None,
    )
    if system_template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    overrides = await list_templates_handler.handle(
        ListTemplatesQuery(usecase=normalized_usecase)
    )
    override_by_part = {override.key: override for override in overrides}

    return TemplateDetailSchema(
        usecase=system_template.usecase,
        name=system_template.name,
        parts=[
            TemplatePartDetailSchema(
                part=part.part,
                system_content=part.content,
                override=map_template_to_schema(override_by_part[part.part])
                if part.part in override_by_part
                else None,
            )
            for part in system_template.parts
        ],
    )


@router.post("/templates/create", response_model=TemplateSchema)
async def create_template_override(
    template_data: TemplateCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    list_system_templates_handler: Annotated[
        ListSystemTemplatesHandler, Depends(get_query_handler(ListSystemTemplatesHandler))
    ],
    create_template_handler: Annotated[
        CreateTemplateHandler, Depends(get_command_handler(CreateTemplateHandler))
    ],
) -> TemplateSchema:
    """Create a new template override."""
    normalized_usecase = template_data.usecase.strip().strip("/")
    normalized_part = template_data.key.strip().strip("/")
    system_templates = await list_system_templates_handler.handle(
        ListSystemTemplatesQuery()
    )
    system_template = next(
        (
            template
            for template in system_templates
            if template.usecase == normalized_usecase
        ),
        None,
    )
    if system_template is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template usecase must match a system template",
        )

    system_parts = {
        part.part
        for part in system_template.parts
    }
    if normalized_part not in system_parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template part must match a system template part",
        )

    default_name = (
        f"{template_display_name(normalized_usecase)} "
        f"{template_display_name(normalized_part)}"
    )
    template = TemplateEntity(
        user_id=user.id,
        usecase=normalized_usecase,
        key=normalized_part,
        name=template_data.name or default_name,
        description=template_data.description,
        content=template_data.content,
    )
    created = await create_template_handler.handle(
        CreateTemplateCommand(template=template)
    )
    return map_template_to_schema(created)


@router.put("/templates/{template_id}", response_model=TemplateSchema)
async def update_template_override(
    template_id: UUID,
    update_data: TemplateUpdateSchema,
    update_template_handler: Annotated[
        UpdateTemplateHandler, Depends(get_command_handler(UpdateTemplateHandler))
    ],
) -> TemplateSchema:
    """Update a template override."""
    update_object = TemplateUpdateObject(
        name=update_data.name,
        description=update_data.description,
        content=update_data.content,
    )
    updated = await update_template_handler.handle(
        UpdateTemplateCommand(template_id=template_id, update_data=update_object)
    )
    return map_template_to_schema(updated)


@router.delete("/templates/{template_id}", status_code=200)
async def delete_template_override(
    template_id: UUID,
    delete_template_handler: Annotated[
        DeleteTemplateHandler, Depends(get_command_handler(DeleteTemplateHandler))
    ],
) -> None:
    """Delete a template override."""
    await delete_template_handler.handle(DeleteTemplateCommand(template_id=template_id))


@router.post("/templates/preview", response_model=TemplatePreviewSchema)
async def preview_template(
    request: TemplatePreviewRequestSchema,
    preview_template_handler: Annotated[
        PreviewTemplateHandler, Depends(get_query_handler(PreviewTemplateHandler))
    ],
) -> TemplatePreviewSchema:
    """Preview rendered template content using current context."""
    preview = await preview_template_handler.handle(
        PreviewTemplateQuery(usecase=request.usecase.strip().strip("/"))
    )
    return TemplatePreviewSchema(
        system_prompt=preview.system_prompt,
        context_prompt=preview.context_prompt,
        ask_prompt=preview.ask_prompt,
        context_data=preview.context_data,
    )
