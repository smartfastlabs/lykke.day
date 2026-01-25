from datetime import UTC, date, datetime, time
from uuid import uuid4

from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.domain import value_objects
from lykke.domain.entities import (
    BrainDumpEntity,
    CalendarEntryEntity,
    DayEntity,
    DayTemplateEntity,
    FactoidEntity,
    MessageEntity,
    PushNotificationEntity,
    TaskEntity,
)


def test_serialize_day_context_with_llm_prompt_data() -> None:
    user_id = uuid4()
    current_time = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    day_date = date(2025, 1, 1)
    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )
    day = DayEntity.create_for_date(day_date, user_id=user_id, template=template)
    day.tags = [value_objects.DayTag.WORKDAY]
    day.high_level_plan = value_objects.HighLevelPlan(
        title="Focus",
        text="Deep work on core project",
        intentions=["Ship feature"],
    )
    day.reminders.append(
        value_objects.Reminder(
            name="Call mom",
            status=value_objects.ReminderStatus.INCOMPLETE,
            created_at=current_time,
        )
    )
    brain_dump_item = BrainDumpEntity(
        user_id=user_id,
        date=day_date,
        text="Buy milk",
        status=value_objects.BrainDumpItemStatus.ACTIVE,
        created_at=current_time,
    )

    task_schedule = value_objects.TaskSchedule(
        start_time=time(10, 0),
        end_time=time(11, 0),
        timing_type=value_objects.TimingType.FIXED_TIME,
    )
    task = TaskEntity(
        user_id=user_id,
        scheduled_date=day_date,
        name="Finish report",
        status=value_objects.TaskStatus.NOT_STARTED,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
        schedule=task_schedule,
    )

    calendar_entry = CalendarEntryEntity(
        user_id=user_id,
        name="Team sync",
        calendar_id=uuid4(),
        platform_id="evt_1",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
        ends_at=datetime(2025, 1, 1, 14, 0, tzinfo=UTC),
        frequency=value_objects.TaskFrequency.ONCE,
        category=value_objects.EventCategory.WORK,
    )

    message = MessageEntity(
        conversation_id=uuid4(),
        role=value_objects.MessageRole.USER,
        content="Hello!",
        meta={"source": "test"},
        created_at=current_time,
    )

    factoid = FactoidEntity(
        user_id=user_id,
        factoid_type=value_objects.FactoidType.SEMANTIC,
        content="Has a dog named Oakley",
        criticality=value_objects.FactoidCriticality.IMPORTANT,
    )

    llm_snapshot = value_objects.LLMRunResultSnapshot(
        tool_calls=[
            value_objects.LLMToolCallResultSnapshot(
                tool_name="decide_notification",
                arguments={"should_notify": True},
                result=None,
            )
        ],
        prompt_context={"day": {"id": str(day.id)}},
        current_time=current_time,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
        system_prompt="system prompt",
        context_prompt="context prompt",
        ask_prompt="ask prompt",
        tools_prompt="tools prompt",
        referenced_entities=[
            value_objects.LLMReferencedEntitySnapshot(
                entity_type="day",
                entity_id=day.id,
            )
        ],
    )

    push_notification = PushNotificationEntity(
        user_id=user_id,
        push_subscription_ids=[uuid4()],
        content='{"title": "Hello", "body": "World"}',
        status="success",
        message="Summary",
        priority="high",
        triggered_by="scheduled",
        llm_snapshot=llm_snapshot,
        sent_at=current_time,
    )

    context = value_objects.LLMPromptContext(
        day=day,
        tasks=[task],
        calendar_entries=[calendar_entry],
        brain_dump_items=[brain_dump_item],
        factoids=[factoid],
        messages=[message],
        push_notifications=[push_notification],
    )

    serialized = serialize_day_context(context, current_time=current_time)

    assert serialized["current_time"] == current_time.isoformat()
    assert serialized["day"]["id"] == str(day.id)
    assert serialized["day"]["tags"] == ["WORKDAY"]
    assert serialized["high_level_plan"]["title"] == "Focus"

    assert serialized["tasks"][0]["id"] == str(task.id)
    assert serialized["tasks"][0]["schedule"]["start_time"] == "10:00:00"
    assert serialized["tasks"][0]["minutes_until_start"] == 60

    assert serialized["calendar_entries"][0]["id"] == str(calendar_entry.id)
    assert serialized["calendar_entries"][0]["minutes_until_start"] == 240

    assert serialized["reminders"][0]["created_at"] == current_time.isoformat()
    assert serialized["brain_dump_items"][0]["created_at"] == current_time.isoformat()

    assert serialized["factoids"][0]["content"] == "Has a dog named Oakley"
    assert serialized["factoids"][0]["criticality"] == "important"

    assert serialized["messages"][0]["role"] == "user"
    assert serialized["messages"][0]["meta"]["source"] == "test"

    notification = serialized["push_notifications"][0]
    assert notification["content"]["title"] == "Hello"
    assert notification["push_subscription_ids"][0] == str(
        push_notification.push_subscription_ids[0]
    )
    assert notification["priority"] == "high"
    assert notification["llm_snapshot"]["llm_provider"] == "anthropic"
    assert notification["llm_snapshot"]["tools_prompt"] == "tools prompt"
