"""Router for usecase configs."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from lykke.application.commands.usecase_config import (
    CreateUseCaseConfigCommand,
    CreateUseCaseConfigHandler,
    DeleteUseCaseConfigCommand,
    DeleteUseCaseConfigHandler,
)
from lykke.application.llm import render_system_prompt
from lykke.application.queries import (
    PreviewLLMSnapshotHandler,
    PreviewLLMSnapshotQuery,
)
from lykke.application.queries.usecase_config import (
    GetUseCaseConfigHandler,
    GetUseCaseConfigQuery,
)
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    NotificationUseCaseConfigSchema,
)
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user

router = APIRouter()


@router.get(
    "/usecase-configs/{usecase:str}",
    response_model=NotificationUseCaseConfigSchema,
)
async def get_usecase_config(
    usecase: str,
    _user: Annotated[UserEntity, Depends(get_current_user)],
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> NotificationUseCaseConfigSchema:
    """Get usecase config by usecase key."""
    query_handler = query_factory.create(GetUseCaseConfigHandler)
    config = await query_handler.handle(GetUseCaseConfigQuery(usecase=usecase))
    if config:
        user_amendments = config.config.get("user_amendments", [])
        if not isinstance(user_amendments, list):
            user_amendments = []
        send_acknowledgment = config.config.get("send_acknowledgment")
        if not isinstance(send_acknowledgment, bool):
            send_acknowledgment = None

        rendered_prompt = await render_system_prompt(
            usecase=usecase,
            user=_user,
            usecase_config_ro_repo=query_factory.ro_repos.usecase_config_ro_repo,
        )

        return NotificationUseCaseConfigSchema(
            user_amendments=user_amendments,
            rendered_prompt=rendered_prompt,
            send_acknowledgment=send_acknowledgment,
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
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> NotificationUseCaseConfigSchema:
    """Create or update usecase config."""
    create_handler = command_factory.create(CreateUseCaseConfigHandler)
    query_handler = query_factory.create(GetUseCaseConfigHandler)
    existing_config = await query_handler.handle(GetUseCaseConfigQuery(usecase=usecase))
    config_dict = dict(existing_config.config) if existing_config else {}
    config_dict["user_amendments"] = config_data.user_amendments or []
    if config_data.send_acknowledgment is not None:
        config_dict["send_acknowledgment"] = config_data.send_acknowledgment

    await create_handler.handle(
        CreateUseCaseConfigCommand(
            user=user,
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
        send_acknowledgment = saved_config.config.get("send_acknowledgment")
        if not isinstance(send_acknowledgment, bool):
            send_acknowledgment = None

        rendered_prompt = await render_system_prompt(
            usecase=usecase,
            user=user,
            usecase_config_ro_repo=query_factory.ro_repos.usecase_config_ro_repo,
        )

        return NotificationUseCaseConfigSchema(
            user_amendments=user_amendments,
            rendered_prompt=rendered_prompt,
            send_acknowledgment=send_acknowledgment,
        )

    return config_data


@router.get(
    "/usecase-configs/{usecase:str}/llm-preview",
    response_model=dict[str, Any] | None,
)
async def get_llm_snapshot_preview(
    usecase: str,
    _user: Annotated[UserEntity, Depends(get_current_user)],
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> dict[str, Any] | None:
    """Build a synthetic LLM snapshot preview for a usecase."""
    query_handler = query_factory.create(PreviewLLMSnapshotHandler)
    snapshot = await query_handler.handle(PreviewLLMSnapshotQuery(usecase=usecase))
    if snapshot is None:
        return None
    return dataclass_to_json_dict(snapshot)


@router.delete("/usecase-configs/{usecase_config_id}", status_code=200)
async def delete_usecase_config(
    usecase_config_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a usecase config."""
    delete_handler = command_factory.create(DeleteUseCaseConfigHandler)
    await delete_handler.handle(
        DeleteUseCaseConfigCommand(usecase_config_id=usecase_config_id)
    )
