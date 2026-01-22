"""Router for usecase configs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from lykke.application.commands.usecase_config import (
    CreateUseCaseConfigCommand,
    CreateUseCaseConfigHandler,
    DeleteUseCaseConfigCommand,
    DeleteUseCaseConfigHandler,
)
from lykke.application.queries.generate_usecase_prompt import (
    GenerateUseCasePromptHandler,
    GenerateUseCasePromptQuery,
)
from lykke.application.queries.usecase_config import (
    GetUseCaseConfigHandler,
    GetUseCaseConfigQuery,
)
from lykke.domain.entities import UseCaseConfigEntity, UserEntity
from lykke.presentation.api.schemas import (
    NotificationUseCaseConfigSchema,
    UseCaseConfigCreateSchema,
    UseCaseConfigSchema,
)

from .dependencies.factories import get_command_handler, get_query_handler
from .dependencies.user import get_current_user

router = APIRouter()


def map_usecase_config_to_schema(config: UseCaseConfigEntity) -> UseCaseConfigSchema:
    """Map UseCaseConfigEntity to UseCaseConfigSchema."""
    return UseCaseConfigSchema(
        id=config.id,
        user_id=config.user_id,
        usecase=config.usecase,
        config=config.config,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get(
    "/usecase-configs/{usecase:str}",
    response_model=NotificationUseCaseConfigSchema,
)
async def get_usecase_config(
    usecase: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    query_handler: Annotated[
        GetUseCaseConfigHandler, Depends(get_query_handler(GetUseCaseConfigHandler))
    ],
    prompt_handler: Annotated[
        GenerateUseCasePromptHandler,
        Depends(get_query_handler(GenerateUseCasePromptHandler)),
    ],
) -> NotificationUseCaseConfigSchema:
    """Get usecase config by usecase key."""
    config = await query_handler.handle(GetUseCaseConfigQuery(usecase=usecase))
    if config:
        user_amendments = config.config.get("user_amendments", [])
        if not isinstance(user_amendments, list):
            user_amendments = []

        prompt_result = await prompt_handler.handle(
            GenerateUseCasePromptQuery(
                usecase=usecase,
                include_context=False,
                include_ask=False,
            )
        )
        rendered_prompt = prompt_result.system_prompt

        return NotificationUseCaseConfigSchema(
            user_amendments=user_amendments,
            rendered_prompt=rendered_prompt,
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Usecase config '{usecase}' not found",
    )


@router.put(
    "/usecase-configs/{usecase:str}",
    response_model=NotificationUseCaseConfigSchema,
)
async def update_usecase_config(
    usecase: str,
    config_data: NotificationUseCaseConfigSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreateUseCaseConfigHandler,
        Depends(get_command_handler(CreateUseCaseConfigHandler)),
    ],
    query_handler: Annotated[
        GetUseCaseConfigHandler, Depends(get_query_handler(GetUseCaseConfigHandler))
    ],
    prompt_handler: Annotated[
        GenerateUseCasePromptHandler,
        Depends(get_query_handler(GenerateUseCasePromptHandler)),
    ],
) -> NotificationUseCaseConfigSchema:
    """Create or update usecase config."""
    config_dict = {"user_amendments": config_data.user_amendments or []}

    await create_handler.handle(
        CreateUseCaseConfigCommand(
            user_id=user.id,
            usecase=usecase,
            config=config_dict,
        )
    )

    # Fetch and return the saved config using query handler
    saved_config = await query_handler.handle(GetUseCaseConfigQuery(usecase=usecase))
    if saved_config:
        user_amendments = saved_config.config.get("user_amendments", [])
        if not isinstance(user_amendments, list):
            user_amendments = []

        prompt_result = await prompt_handler.handle(
            GenerateUseCasePromptQuery(
                usecase=usecase,
                include_context=False,
                include_ask=False,
            )
        )
        rendered_prompt = prompt_result.system_prompt

        return NotificationUseCaseConfigSchema(
            user_amendments=user_amendments,
            rendered_prompt=rendered_prompt,
        )

    return config_data


@router.delete("/usecase-configs/{usecase_config_id}", status_code=200)
async def delete_usecase_config(
    usecase_config_id: UUID,
    delete_handler: Annotated[
        DeleteUseCaseConfigHandler,
        Depends(get_command_handler(DeleteUseCaseConfigHandler)),
    ],
) -> None:
    """Delete a usecase config."""
    await delete_handler.handle(
        DeleteUseCaseConfigCommand(usecase_config_id=usecase_config_id)
    )
