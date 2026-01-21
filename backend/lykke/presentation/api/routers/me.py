"""Endpoints for retrieving the current authenticated user."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.application.queries import GetDayContextHandler, GetDayContextQuery
from lykke.application.commands.day import (
    AddBrainDumpItemToDayCommand,
    AddBrainDumpItemToDayHandler,
    AddReminderToDayCommand,
    AddReminderToDayHandler,
    RemoveBrainDumpItemCommand,
    RemoveBrainDumpItemHandler,
    RemoveReminderCommand,
    RemoveReminderHandler,
    UpdateBrainDumpItemStatusCommand,
    UpdateBrainDumpItemStatusHandler,
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import (
    UserSetting,
    UserUpdateObject,
)
from lykke.presentation.api.schemas import (
    UserSchema,
    UserUpdateSchema,
    DayContextSchema,
)
from lykke.presentation.api.schemas.mappers import map_user_to_schema, map_day_context_to_schema
from lykke.core.utils.dates import get_current_date

from .dependencies.factories import get_command_handler
from .dependencies.user import get_current_user
from .dependencies.services import (
    day_context_handler,
    get_add_brain_dump_item_handler,
    get_add_reminder_to_day_handler,
    get_remove_brain_dump_item_handler,
    get_remove_reminder_handler,
    get_update_brain_dump_item_status_handler,
    get_update_reminder_status_handler,
)

router = APIRouter()


@router.get("", response_model=UserSchema)
async def get_current_user_profile(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserSchema:
    """Return the currently authenticated user."""
    return map_user_to_schema(user)


@router.put("", response_model=UserSchema)
async def update_current_user_profile(
    update_data: UserUpdateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    update_user_handler: Annotated[
        UpdateUserHandler, Depends(get_command_handler(UpdateUserHandler))
    ],
) -> UserSchema:
    """Update the current authenticated user."""
    settings = None
    if update_data.settings is not None:
        current_settings = user.settings or UserSetting()
        settings_fields = update_data.settings.model_fields_set
        template_defaults = (
            update_data.settings.template_defaults
            if "template_defaults" in settings_fields
            and update_data.settings.template_defaults is not None
            else current_settings.template_defaults
        )
        llm_provider = (
            update_data.settings.llm_provider
            if "llm_provider" in settings_fields
            else current_settings.llm_provider
        )
        timezone = (
            update_data.settings.timezone
            if "timezone" in settings_fields
            else current_settings.timezone
        )
        settings = UserSetting(
            template_defaults=template_defaults,
            llm_provider=llm_provider,
            timezone=timezone,
        )

    update_object = UserUpdateObject(
        phone_number=update_data.phone_number,
        status=update_data.status,
        is_active=update_data.is_active,
        is_superuser=update_data.is_superuser,
        is_verified=update_data.is_verified,
        settings=settings,
    )
    updated_user = await update_user_handler.handle(UpdateUserCommand(update_data=update_object))
    return map_user_to_schema(updated_user)


# ============================================================================
# Today's Reminders
# ============================================================================


@router.post("/today/reminders", response_model=DayContextSchema)
async def add_reminder_to_today(
    name: str,
    handler: Annotated[AddReminderToDayHandler, Depends(get_add_reminder_to_day_handler)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Add a reminder to today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(AddReminderToDayCommand(date=date, reminder=name))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


@router.patch("/today/reminders/{reminder_id}", response_model=DayContextSchema)
async def update_today_reminder_status(
    reminder_id: UUID,
    status: value_objects.ReminderStatus,
    handler: Annotated[
        UpdateReminderStatusHandler, Depends(get_update_reminder_status_handler)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Update a reminder's status for today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(UpdateReminderStatusCommand(date=date, reminder_id=reminder_id, status=status))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


@router.delete("/today/reminders/{reminder_id}", response_model=DayContextSchema)
async def remove_reminder_from_today(
    reminder_id: UUID,
    handler: Annotated[RemoveReminderHandler, Depends(get_remove_reminder_handler)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Remove a reminder from today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(RemoveReminderCommand(date=date, reminder_id=reminder_id))
    # Get the full context to return
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


# ============================================================================
# Today's Brain Dump
# ============================================================================


@router.post("/today/brain-dump", response_model=DayContextSchema)
async def add_brain_dump_item_to_today(
    text: str,
    handler: Annotated[
        AddBrainDumpItemToDayHandler, Depends(get_add_brain_dump_item_handler)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Add a brain dump item to today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(AddBrainDumpItemToDayCommand(date=date, text=text))
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


@router.patch("/today/brain-dump/{item_id}", response_model=DayContextSchema)
async def update_brain_dump_item_status(
    item_id: UUID,
    status: value_objects.BrainDumpItemStatus,
    handler: Annotated[
        UpdateBrainDumpItemStatusHandler,
        Depends(get_update_brain_dump_item_status_handler),
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Update a brain dump item's status for today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(
        UpdateBrainDumpItemStatusCommand(date=date, item_id=item_id, status=status)
    )
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


@router.delete("/today/brain-dump/{item_id}", response_model=DayContextSchema)
async def remove_brain_dump_item_from_today(
    item_id: UUID,
    handler: Annotated[
        RemoveBrainDumpItemHandler, Depends(get_remove_brain_dump_item_handler)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    day_context_handler_instance: Annotated[
        GetDayContextHandler, Depends(day_context_handler)
    ],
) -> DayContextSchema:
    """Remove a brain dump item from today."""
    date = get_current_date(user.settings.timezone)
    await handler.handle(RemoveBrainDumpItemCommand(date=date, item_id=item_id))
    context = await day_context_handler_instance.handle(GetDayContextQuery(date=date))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


