"""Mapper functions to convert domain entities to API schemas."""

from dataclasses import asdict

from lykke.core.utils.dates import resolve_timezone
from lykke.domain import value_objects
from lykke.domain.entities import (
    AuditableEntity,
    AuditLogEntity,
    BotPersonalityEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
    ConversationEntity,
    DayEntity,
    DayTemplateEntity,
    FactoidEntity,
    MessageEntity,
    PushNotificationEntity,
    PushSubscriptionEntity,
    RoutineEntity,
    TaskDefinitionEntity,
    TaskEntity,
    TimeBlockDefinitionEntity,
    UseCaseConfigEntity,
    UserEntity,
)
from lykke.presentation.api.schemas import (
    ActionSchema,
    AuditableSchema,
    AuditLogSchema,
    BotPersonalitySchema,
    BrainDumpItemSchema,
    CalendarEntrySchema,
    CalendarEntrySeriesSchema,
    CalendarSchema,
    ConversationSchema,
    DayContextSchema,
    DaySchema,
    DayTemplateSchema,
    DayTemplateTimeBlockSchema,
    FactoidSchema,
    HighLevelPlanSchema,
    MessageSchema,
    PushSubscriptionSchema,
    ReminderSchema,
    RoutineSchema,
    SyncSubscriptionSchema,
    TaskDefinitionSchema,
    TaskScheduleSchema,
    TaskSchema,
    TimeBlockDefinitionSchema,
    UseCaseConfigSchema,
    UserSchema,
    UserSettingsSchema,
)
from lykke.presentation.api.schemas.push_notification import PushNotificationSchema


def map_action_to_schema(action: value_objects.Action) -> ActionSchema:
    """Convert Action entity to Action schema."""
    return ActionSchema(**asdict(action))


def map_reminder_to_schema(reminder: value_objects.Reminder) -> ReminderSchema:
    """Convert Reminder value object to Reminder schema."""
    return ReminderSchema(
        id=reminder.id,
        name=reminder.name,
        status=reminder.status,
        created_at=reminder.created_at,
    )


def map_brain_dump_item_to_schema(
    item: value_objects.BrainDumpItem,
) -> BrainDumpItemSchema:
    """Convert BrainDumpItem value object to schema."""
    return BrainDumpItemSchema(
        id=item.id,
        text=item.text,
        status=item.status,
        created_at=item.created_at,
    )


def map_task_definition_to_schema(
    task_definition: TaskDefinitionEntity,
) -> TaskDefinitionSchema:
    """Convert TaskDefinition data object to TaskDefinition schema."""
    return TaskDefinitionSchema(
        id=task_definition.id,
        user_id=task_definition.user_id,
        name=task_definition.name,
        description=task_definition.description,
        type=task_definition.type,
    )


def map_time_block_definition_to_schema(
    time_block_definition: TimeBlockDefinitionEntity,
) -> TimeBlockDefinitionSchema:
    """Convert TimeBlockDefinition data object to TimeBlockDefinition schema."""
    return TimeBlockDefinitionSchema(
        id=time_block_definition.id,
        user_id=time_block_definition.user_id,
        name=time_block_definition.name,
        description=time_block_definition.description,
        type=time_block_definition.type,
        category=time_block_definition.category,
    )


def map_task_schedule_to_schema(
    schedule: value_objects.TaskSchedule | None,
) -> TaskScheduleSchema | None:
    """Convert TaskSchedule value object to TaskSchedule schema."""
    if schedule is None:
        return None
    # Convert dataclass to schema using field mapping
    return TaskScheduleSchema(
        available_time=schedule.available_time,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        timing_type=schedule.timing_type,
    )


def map_task_to_schema(task: TaskEntity) -> TaskSchema:
    """Convert Task entity to Task schema."""
    # Convert nested entities
    action_schemas = [map_action_to_schema(action) for action in task.actions]
    schedule_schema = map_task_schedule_to_schema(task.schedule)

    return TaskSchema(
        id=task.id,
        user_id=task.user_id,
        scheduled_date=task.scheduled_date,
        name=task.name,
        status=task.status,
        type=task.type,
        description=task.description,
        category=task.category,
        frequency=task.frequency,
        completed_at=task.completed_at,
        schedule=schedule_schema,
        routine_id=task.routine_id,
        tags=task.tags,
        actions=action_schemas,
    )


def map_day_template_to_schema(
    template: DayTemplateEntity,
) -> DayTemplateSchema:
    """Convert DayTemplate data object to DayTemplate schema."""
    time_blocks_schema = [
        DayTemplateTimeBlockSchema(
            time_block_definition_id=tb.time_block_definition_id,
            start_time=tb.start_time,
            end_time=tb.end_time,
            name=tb.name,
        )
        for tb in template.time_blocks
    ]

    return DayTemplateSchema(
        id=template.id,
        user_id=template.user_id,
        slug=template.slug,
        start_time=template.start_time,
        end_time=template.end_time,
        icon=template.icon,
        routine_ids=template.routine_ids,
        time_blocks=time_blocks_schema,
        high_level_plan=(
            HighLevelPlanSchema(
                title=template.high_level_plan.title,
                text=template.high_level_plan.text,
                intentions=template.high_level_plan.intentions,
            )
            if template.high_level_plan
            else None
        ),
    )


def map_day_to_schema(day: DayEntity) -> DaySchema:
    """Convert Day entity to Day schema."""
    template_schema = map_day_template_to_schema(day.template) if day.template else None

    reminder_schemas = [map_reminder_to_schema(reminder) for reminder in day.reminders]
    brain_dump_item_schemas = [
        map_brain_dump_item_to_schema(item) for item in day.brain_dump_items
    ]

    return DaySchema(
        id=day.id,
        user_id=day.user_id,
        date=day.date,
        status=day.status,
        scheduled_at=day.scheduled_at,
        starts_at=day.starts_at,
        ends_at=day.ends_at,
        tags=day.tags,
        template=template_schema,
        reminders=reminder_schemas,
        brain_dump_items=brain_dump_item_schemas,
        high_level_plan=(
            HighLevelPlanSchema(
                title=day.high_level_plan.title,
                text=day.high_level_plan.text,
                intentions=day.high_level_plan.intentions,
            )
            if day.high_level_plan
            else None
        ),
    )


def map_calendar_entry_to_schema(
    entry: CalendarEntryEntity,
    *,
    user_timezone: str | None = None,
) -> CalendarEntrySchema:
    """Convert CalendarEntry entity to CalendarEntry schema."""
    action_schemas = [map_action_to_schema(action) for action in entry.actions]
    entry_date = entry.starts_at.astimezone(resolve_timezone(user_timezone)).date()

    return CalendarEntrySchema(
        id=entry.id,
        user_id=entry.user_id,
        name=entry.name,
        calendar_id=entry.calendar_id,
        platform_id=entry.platform_id,
        platform=entry.platform,
        status=entry.status,
        starts_at=entry.starts_at,
        frequency=entry.frequency,
        category=entry.category,
        ends_at=entry.ends_at,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        actions=action_schemas,
        date=entry_date,
    )


def map_day_context_to_schema(
    context: value_objects.DayContext,
    *,
    user_timezone: str | None = None,
) -> DayContextSchema:
    """Convert DayContext value object to DayContext schema."""
    day_schema = map_day_to_schema(context.day)
    calendar_entry_schemas = [
        map_calendar_entry_to_schema(entry, user_timezone=user_timezone)
        for entry in context.calendar_entries
    ]
    task_schemas = [map_task_to_schema(task) for task in context.tasks]

    return DayContextSchema(
        day=day_schema,
        calendar_entries=calendar_entry_schemas,
        tasks=task_schemas,
    )


def map_calendar_entry_series_to_schema(
    series: CalendarEntrySeriesEntity,
) -> CalendarEntrySeriesSchema:
    """Convert CalendarEntrySeries entity to schema."""
    return CalendarEntrySeriesSchema(
        id=series.id,
        user_id=series.user_id,
        calendar_id=series.calendar_id,
        name=series.name,
        platform_id=series.platform_id,
        platform=series.platform,
        frequency=series.frequency,
        event_category=series.event_category,
        recurrence=series.recurrence or [],
        starts_at=series.starts_at,
        ends_at=series.ends_at,
        created_at=series.created_at,
        updated_at=series.updated_at,
    )


def map_push_subscription_to_schema(
    subscription: PushSubscriptionEntity,
) -> PushSubscriptionSchema:
    """Convert PushSubscription entity to PushSubscription schema."""
    return PushSubscriptionSchema(
        id=subscription.id,
        user_id=subscription.user_id,
        endpoint=subscription.endpoint,
        p256dh=subscription.p256dh,
        auth=subscription.auth,
        device_name=subscription.device_name,
        created_at=subscription.created_at,
    )


def map_push_notification_to_schema(
    notification: PushNotificationEntity,
) -> PushNotificationSchema:
    """Convert PushNotification entity to PushNotification schema."""
    return PushNotificationSchema(
        id=notification.id,
        user_id=notification.user_id,
        push_subscription_ids=notification.push_subscription_ids,
        content=notification.content,
        status=notification.status,
        error_message=notification.error_message,
        sent_at=notification.sent_at,
        message=notification.message,
        priority=notification.priority,
        reason=notification.reason,
        day_context_snapshot=notification.day_context_snapshot,
        message_hash=notification.message_hash,
        triggered_by=notification.triggered_by,
        llm_provider=notification.llm_provider,
    )


def map_routine_to_schema(routine: RoutineEntity) -> RoutineSchema:
    """Convert Routine entity to Routine schema."""
    from .routine import RecurrenceScheduleSchema, RoutineTaskSchema

    # Convert routine schedule
    routine_schedule_schema = RecurrenceScheduleSchema(
        frequency=routine.routine_schedule.frequency,
        weekdays=routine.routine_schedule.weekdays,
        day_number=routine.routine_schedule.day_number,
    )

    # Convert tasks
    task_schemas = []
    for task in routine.tasks:
        schedule_schema = None
        if task.schedule:
            schedule_schema = map_task_schedule_to_schema(task.schedule)

        task_schedule_schema = None
        if task.task_schedule:
            task_schedule_schema = RecurrenceScheduleSchema(
                frequency=task.task_schedule.frequency,
                weekdays=task.task_schedule.weekdays,
                day_number=task.task_schedule.day_number,
            )

        task_schema = RoutineTaskSchema(
            id=task.id,
            task_definition_id=task.task_definition_id,
            name=task.name,
            schedule=schedule_schema,
            task_schedule=task_schedule_schema,
        )
        task_schemas.append(task_schema)

    return RoutineSchema(
        id=routine.id,
        user_id=routine.user_id,
        name=routine.name,
        category=routine.category,
        routine_schedule=routine_schedule_schema,
        description=routine.description,
        tasks=task_schemas,
    )


def map_calendar_to_schema(calendar: CalendarEntity) -> CalendarSchema:
    """Convert Calendar entity to Calendar schema."""
    sync_subscription = None
    if calendar.sync_subscription:
        sync_subscription = SyncSubscriptionSchema(**asdict(calendar.sync_subscription))

    return CalendarSchema(
        id=calendar.id,
        user_id=calendar.user_id,
        name=calendar.name,
        auth_token_id=calendar.auth_token_id,
        platform_id=calendar.platform_id,
        platform=calendar.platform,
        default_event_category=calendar.default_event_category,
        last_sync_at=calendar.last_sync_at,
        sync_subscription=sync_subscription,
        sync_subscription_id=calendar.sync_subscription_id,
        sync_enabled=calendar.sync_subscription is not None,
    )


def map_user_to_schema(user: UserEntity) -> UserSchema:
    """Convert User entity to User schema."""
    settings_dict = asdict(user.settings)
    settings_schema = UserSettingsSchema(**settings_dict)

    return UserSchema(
        id=user.id,
        email=user.email,
        phone_number=user.phone_number,
        status=user.status,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        settings=settings_schema,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def map_use_case_config_to_schema(
    config: UseCaseConfigEntity,
) -> UseCaseConfigSchema:
    """Convert UseCaseConfig entity to UseCaseConfig schema."""
    return UseCaseConfigSchema(
        id=config.id,
        user_id=config.user_id,
        usecase=config.usecase,
        config=config.config,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def map_message_to_schema(message: MessageEntity) -> MessageSchema:
    """Convert Message entity to Message schema."""
    return MessageSchema(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role.value,
        content=message.content,
        meta=message.meta,
        created_at=message.created_at,
    )


def map_conversation_to_schema(conversation: ConversationEntity) -> ConversationSchema:
    """Convert Conversation entity to Conversation schema."""
    return ConversationSchema(
        id=conversation.id,
        user_id=conversation.user_id,
        bot_personality_id=conversation.bot_personality_id,
        channel=conversation.channel.value,
        status=conversation.status.value,
        llm_provider=conversation.llm_provider.value,
        context=conversation.context,
        created_at=conversation.created_at,
        last_message_at=conversation.last_message_at,
    )


def map_audit_log_to_schema(audit_log: AuditLogEntity) -> AuditLogSchema:
    """Convert AuditLog entity to AuditLog schema."""
    return AuditLogSchema(
        id=audit_log.id,
        user_id=audit_log.user_id,
        activity_type=audit_log.activity_type,
        occurred_at=audit_log.occurred_at,
        entity_id=audit_log.entity_id,
        entity_type=audit_log.entity_type,
        meta=audit_log.meta,
    )


def map_auditable_to_schema(_auditable: AuditableEntity) -> AuditableSchema:
    """Convert Auditable marker interface to Auditable schema.

    Note: AuditableEntity is a marker interface with no fields,
    so this returns an empty schema instance.
    """
    return AuditableSchema()


def map_bot_personality_to_schema(
    bot_personality: BotPersonalityEntity,
) -> BotPersonalitySchema:
    """Convert BotPersonality entity to BotPersonality schema."""
    return BotPersonalitySchema(
        id=bot_personality.id,
        user_id=bot_personality.user_id,
        name=bot_personality.name,
        base_bot_personality_id=bot_personality.base_bot_personality_id,
        system_prompt=bot_personality.system_prompt,
        user_amendments=bot_personality.user_amendments,
        meta=bot_personality.meta,
        created_at=bot_personality.created_at,
    )


def map_factoid_to_schema(factoid: FactoidEntity) -> FactoidSchema:
    """Convert Factoid entity to Factoid schema."""
    return FactoidSchema(
        id=factoid.id,
        user_id=factoid.user_id,
        conversation_id=factoid.conversation_id,
        factoid_type=factoid.factoid_type.value,
        criticality=factoid.criticality.value,
        content=factoid.content,
        embedding=factoid.embedding,
        ai_suggested=factoid.ai_suggested,
        user_confirmed=factoid.user_confirmed,
        last_accessed=factoid.last_accessed,
        access_count=factoid.access_count,
        meta=factoid.meta,
        created_at=factoid.created_at,
    )
