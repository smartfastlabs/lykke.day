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
from lykke.domain import value_objects
from lykke.domain.entities import UseCaseConfigEntity, UserEntity
from lykke.presentation.api.schemas import (
    NotificationUseCaseConfigSchema,
    UseCaseConfigCreateSchema,
    UseCaseConfigSchema,
)

from .dependencies.factories import get_command_handler
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


@router.post("/usecase-configs", response_model=UseCaseConfigSchema)
async def create_or_update_usecase_config(
    config_data: UseCaseConfigCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreateUseCaseConfigHandler, Depends(get_command_handler(CreateUseCaseConfigHandler))
    ],
) -> UseCaseConfigSchema:
    """Create or update a usecase config."""
    normalized_usecase = config_data.usecase.strip().strip("/")
    
    # Validate usecase (for now, only "notification" is supported)
    if normalized_usecase not in ["notification"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported usecase: {normalized_usecase}",
        )
    
    created = await create_handler.handle(
        CreateUseCaseConfigCommand(
            user_id=user.id,
            usecase=normalized_usecase,
            config=config_data.config,
        )
    )
    return map_usecase_config_to_schema(created)


@router.get("/usecase-configs/{usecase:path}", response_model=UseCaseConfigSchema | None)
async def get_usecase_config(
    usecase: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreateUseCaseConfigHandler, Depends(get_command_handler(CreateUseCaseConfigHandler))
    ],
) -> UseCaseConfigSchema | None:
    """Get a usecase config for the current user."""
    normalized_usecase = usecase.strip().strip("/")
    
    # This is a bit of a hack - we use the handler's ro_repo to query
    # In a real implementation, we'd have a query handler for this
    configs = await create_handler.usecase_config_ro_repo.search(
        value_objects.UseCaseConfigQuery(usecase=normalized_usecase)
    )
    if configs:
        return map_usecase_config_to_schema(configs[0])
    return None


@router.delete("/usecase-configs/{usecase_config_id}", status_code=200)
async def delete_usecase_config(
    usecase_config_id: UUID,
    delete_handler: Annotated[
        DeleteUseCaseConfigHandler, Depends(get_command_handler(DeleteUseCaseConfigHandler))
    ],
) -> None:
    """Delete a usecase config."""
    await delete_handler.handle(DeleteUseCaseConfigCommand(usecase_config_id=usecase_config_id))


@router.get("/usecase-configs/notification/config", response_model=NotificationUseCaseConfigSchema)
async def get_notification_config(
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreateUseCaseConfigHandler, Depends(get_command_handler(CreateUseCaseConfigHandler))
    ],
) -> NotificationUseCaseConfigSchema:
    """Get notification usecase config in a typed format."""
    configs = await create_handler.usecase_config_ro_repo.search(
        value_objects.UseCaseConfigQuery(usecase="notification")
    )
    if configs:
        config = configs[0].config
        user_amendments = config.get("user_amendments", [])
        # Ensure it's a list[str]
        if not isinstance(user_amendments, list):
            user_amendments = []
        return NotificationUseCaseConfigSchema(user_amendments=user_amendments)
    return NotificationUseCaseConfigSchema()


@router.put("/usecase-configs/notification/config", response_model=NotificationUseCaseConfigSchema)
async def update_notification_config(
    config_data: NotificationUseCaseConfigSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreateUseCaseConfigHandler, Depends(get_command_handler(CreateUseCaseConfigHandler))
    ],
) -> NotificationUseCaseConfigSchema:
    """Update notification usecase config."""
    # Convert typed schema to dict config
    config_dict = {
        "user_amendments": config_data.user_amendments or []
    }
    
    await create_handler.handle(
        CreateUseCaseConfigCommand(
            user_id=user.id,
            usecase="notification",
            config=config_dict,
        )
    )
    return config_data
