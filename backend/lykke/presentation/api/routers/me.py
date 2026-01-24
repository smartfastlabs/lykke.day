"""Endpoints for retrieving the current authenticated user."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.brain_dump import (
    CreateBrainDumpItemCommand,
    CreateBrainDumpItemHandler,
    DeleteBrainDumpItemCommand,
    DeleteBrainDumpItemHandler,
    UpdateBrainDumpItemStatusCommand,
    UpdateBrainDumpItemStatusHandler,
)
from lykke.application.commands.day import (
    AddReminderToDayCommand,
    AddReminderToDayHandler,
    AddRoutineDefinitionToDayCommand,
    AddRoutineDefinitionToDayHandler,
    RemoveReminderCommand,
    RemoveReminderHandler,
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)
from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.application.queries.list_base_personalities import (
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)
from lykke.core.utils.dates import get_current_date
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserSetting, UserUpdateObject
from lykke.presentation.api.schemas import (
    BasePersonalitySchema,
    BrainDumpItemSchema,
    ReminderSchema,
    TaskSchema,
    UserSchema,
    UserUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import (
    map_brain_dump_item_to_schema,
    map_reminder_to_schema,
    map_task_to_schema,
    map_user_to_schema,
)
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user

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
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> UserSchema:
    """Update the current authenticated user."""
    update_user_handler = command_factory.create(UpdateUserHandler)
    settings = None
    if update_data.settings is not None:
        current_settings = user.settings or UserSetting()
        # Use model_dump to see which fields were actually provided in the request
        # This is more reliable than model_fields_set for optional fields
        provided_settings = update_data.settings.model_dump(exclude_unset=True)
        settings_fields = set(provided_settings.keys())
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
        base_personality_slug = (
            update_data.settings.base_personality_slug
            if "base_personality_slug" in settings_fields
            and update_data.settings.base_personality_slug is not None
            else current_settings.base_personality_slug
        )
        llm_personality_amendments = (
            update_data.settings.llm_personality_amendments
            if "llm_personality_amendments" in settings_fields
            and update_data.settings.llm_personality_amendments is not None
            else current_settings.llm_personality_amendments
        )
        # Handle morning_overview_time - check if it was explicitly set (even if None)
        # Pydantic's model_fields_set includes fields that were explicitly provided
        if "morning_overview_time" in settings_fields:
            morning_overview_time = update_data.settings.morning_overview_time
        else:
            morning_overview_time = current_settings.morning_overview_time
        settings = UserSetting(
            template_defaults=template_defaults,
            llm_provider=llm_provider,
            timezone=timezone,
            base_personality_slug=base_personality_slug,
            llm_personality_amendments=llm_personality_amendments,
            morning_overview_time=morning_overview_time,
        )

    update_object = UserUpdateObject(
        phone_number=update_data.phone_number,
        status=update_data.status,
        is_active=update_data.is_active,
        is_superuser=update_data.is_superuser,
        is_verified=update_data.is_verified,
        settings=settings,
    )
    updated_user = await update_user_handler.handle(
        UpdateUserCommand(update_data=update_object)
    )
    return map_user_to_schema(updated_user)


@router.get("/base-personalities", response_model=list[BasePersonalitySchema])
async def list_base_personalities(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> list[BasePersonalitySchema]:
    """List available base personalities."""
    handler = query_factory.create(ListBasePersonalitiesHandler)
    personalities = await handler.handle(ListBasePersonalitiesQuery())
    return [
        BasePersonalitySchema.model_validate(personality)
        for personality in personalities
    ]


# ============================================================================
# Today's Reminders
# ============================================================================


@router.post("/today/reminders", response_model=ReminderSchema)
async def add_reminder_to_today(
    name: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Add a reminder to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(AddReminderToDayHandler)
    reminder = await handler.handle(AddReminderToDayCommand(date=date, reminder=name))
    return map_reminder_to_schema(reminder)


@router.patch("/today/reminders/{reminder_id}", response_model=ReminderSchema)
async def update_today_reminder_status(
    reminder_id: UUID,
    status: value_objects.ReminderStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Update a reminder's status for today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(UpdateReminderStatusHandler)
    reminder = await handler.handle(
        UpdateReminderStatusCommand(date=date, reminder_id=reminder_id, status=status)
    )
    return map_reminder_to_schema(reminder)


@router.delete("/today/reminders/{reminder_id}", response_model=ReminderSchema)
async def remove_reminder_from_today(
    reminder_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Remove a reminder from today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(RemoveReminderHandler)
    reminder = await handler.handle(
        RemoveReminderCommand(date=date, reminder_id=reminder_id)
    )
    return map_reminder_to_schema(reminder)


# ============================================================================
# Today's Brain Dump
# ============================================================================


@router.post("/today/brain-dump", response_model=BrainDumpItemSchema)
async def add_brain_dump_item_to_today(
    text: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpItemSchema:
    """Add a brain dump item to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(CreateBrainDumpItemHandler)
    item = await handler.handle(CreateBrainDumpItemCommand(date=date, text=text))
    return map_brain_dump_item_to_schema(item)


@router.patch("/today/brain-dump/{item_id}", response_model=BrainDumpItemSchema)
async def update_brain_dump_item_status(
    item_id: UUID,
    status: value_objects.BrainDumpItemStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpItemSchema:
    """Update a brain dump item's status for today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(UpdateBrainDumpItemStatusHandler)
    item = await handler.handle(
        UpdateBrainDumpItemStatusCommand(date=date, item_id=item_id, status=status)
    )
    return map_brain_dump_item_to_schema(item)


@router.delete("/today/brain-dump/{item_id}", response_model=BrainDumpItemSchema)
async def remove_brain_dump_item_from_today(
    item_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpItemSchema:
    """Remove a brain dump item from today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(DeleteBrainDumpItemHandler)
    item = await handler.handle(DeleteBrainDumpItemCommand(date=date, item_id=item_id))
    return map_brain_dump_item_to_schema(item)


# ============================================================================
# Today's Routine Definitions
# ============================================================================


@router.post("/today/routine-definitions", response_model=list[TaskSchema])
async def add_routine_definition_to_today(
    routine_definition_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Add a routine definition's tasks to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(AddRoutineDefinitionToDayHandler)
    tasks = await handler.handle(
        AddRoutineDefinitionToDayCommand(
            date=date,
            routine_definition_id=routine_definition_id,
        )
    )
    return [map_task_to_schema(task) for task in tasks]
