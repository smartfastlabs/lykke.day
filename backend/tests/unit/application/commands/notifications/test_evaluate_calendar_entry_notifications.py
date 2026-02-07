"""Unit tests for CalendarEntryNotificationHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, timedelta
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import pytest
from dobles import allow
from freezegun import freeze_time

from lykke.application.commands.notifications import (
    CalendarEntryNotificationCommand,
    CalendarEntryNotificationHandler,
)
from lykke.application.repositories import (
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import (
    CalendarEntryEntity,
    DayEntity,
    DayTemplateEntity,
    PushNotificationEntity,
    PushSubscriptionEntity,
    UserEntity,
)
from lykke.domain.events.day_events import AlarmTriggeredEvent
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_day_repo_double,
    create_push_subscription_repo_double,
    create_read_only_repos_double,
    create_repo_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@dataclass
class _Recorder:
    commands: list[object]

    async def handle(self, command: object) -> None:
        self.commands.append(command)


class _SmsGateway:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_message(self, phone_number: str, message: str) -> None:
        self.sent.append((phone_number, message))


def _build_user(
    user_id: UUID,
    *,
    timezone: str | None = "UTC",
    phone_number: str | None = "+15555550100",
    rules: list[value_objects.CalendarEntryNotificationRule],
) -> UserEntity:
    settings = value_objects.UserSetting(
        template_defaults=["default"] * 7,
        timezone=timezone,
        calendar_entry_notification_settings=value_objects.CalendarEntryNotificationSettings(
            enabled=True,
            rules=rules,
        ),
    )
    return UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        phone_number=phone_number,
        settings=settings,
    )


def _build_entry(
    user_id: UUID,
    starts_at: datetime,
    *,
    name: str = "Team Sync",
    attendance_status: value_objects.CalendarEntryAttendanceStatus | None = None,
) -> CalendarEntryEntity:
    return CalendarEntryEntity(
        user_id=user_id,
        name=name,
        calendar_id=uuid4(),
        platform_id="platform-1",
        platform="google",
        status="confirmed",
        attendance_status=attendance_status,
        starts_at=starts_at,
        frequency=value_objects.TaskFrequency.ONCE,
    )


def _allow_calendar_entry_search(
    calendar_entry_repo: object, today: dt_date, entry: CalendarEntryEntity
) -> None:
    allow(calendar_entry_repo).search.with_args(
        value_objects.CalendarEntryQuery(date=today)
    ).and_return([entry])
    allow(calendar_entry_repo).search.with_args(
        value_objects.CalendarEntryQuery(date=today + timedelta(days=1))
    ).and_return([])


@pytest.mark.asyncio
@freeze_time("2026-02-01 10:00:00")
async def test_calendar_entry_push_sends_notification() -> None:
    user_id = uuid4()
    now = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
    entry = _build_entry(user_id, now + timedelta(minutes=5))
    rules = [
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.PUSH,
            minutes_before=5,
        )
    ]
    user = _build_user(user_id, rules=rules)

    calendar_entry_repo = create_calendar_entry_repo_double()
    _allow_calendar_entry_search(calendar_entry_repo, now.date(), entry)

    push_subscription_repo = create_push_subscription_repo_double()
    allow(push_subscription_repo).all.and_return(
        [
            PushSubscriptionEntity(
                user_id=user_id,
                endpoint="https://example.com/push/1",
                p256dh="p256dh",
                auth="auth",
            )
        ]
    )

    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    allow(push_notification_repo).search.and_return([])

    message_repo = create_repo_double(MessageRepositoryReadOnlyProtocol)
    allow(message_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo,
        push_subscription_repo=push_subscription_repo,
        push_notification_repo=push_notification_repo,
        message_repo=message_repo,
    )
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)

    recorder = _Recorder(commands=[])
    handler = CalendarEntryNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.send_push_notification_handler = recorder
    handler.sms_gateway = _SmsGateway()

    await handler.handle(CalendarEntryNotificationCommand(user=user))

    assert len(recorder.commands) == 1
    command = recorder.commands[0]
    assert command.triggered_by is not None
    assert command.triggered_by.startswith("calendar_entry_reminder:")
    assert command.message is not None
    assert "Team Sync" in command.message


@pytest.mark.asyncio
@freeze_time("2026-02-01 10:00:00")
async def test_calendar_entry_notifications_skip_when_not_going() -> None:
    user_id = uuid4()
    now = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
    entry = _build_entry(
        user_id,
        now + timedelta(minutes=5),
        attendance_status=value_objects.CalendarEntryAttendanceStatus.NOT_GOING,
    )
    rules = [
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.PUSH,
            minutes_before=5,
        ),
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.TEXT,
            minutes_before=5,
        ),
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.KIOSK_ALARM,
            minutes_before=5,
        ),
    ]
    user = _build_user(user_id, rules=rules)

    calendar_entry_repo = create_calendar_entry_repo_double()
    _allow_calendar_entry_search(calendar_entry_repo, now.date(), entry)

    push_subscription_repo = create_push_subscription_repo_double()
    allow(push_subscription_repo).all.and_return(
        [
            PushSubscriptionEntity(
                user_id=user_id,
                endpoint="https://example.com/push/1",
                p256dh="p256dh",
                auth="auth",
            )
        ]
    )

    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    allow(push_notification_repo).search.and_return([])

    message_repo = create_repo_double(MessageRepositoryReadOnlyProtocol)
    allow(message_repo).search.and_return([])

    day_repo = create_day_repo_double()
    allow(day_repo).get.and_raise(AssertionError("Day repo should not be used"))

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo,
        push_subscription_repo=push_subscription_repo,
        push_notification_repo=push_notification_repo,
        message_repo=message_repo,
        day_repo=day_repo,
    )
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)

    recorder = _Recorder(commands=[])
    sms_gateway = _SmsGateway()
    handler = CalendarEntryNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.send_push_notification_handler = recorder
    handler.sms_gateway = sms_gateway

    await handler.handle(CalendarEntryNotificationCommand(user=user))

    assert recorder.commands == []
    assert sms_gateway.sent == []
    assert uow.added == []


@pytest.mark.asyncio
@freeze_time("2026-02-01 10:00:00")
async def test_calendar_entry_push_dedupes_on_triggered_by() -> None:
    user_id = uuid4()
    now = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
    entry = _build_entry(user_id, now + timedelta(minutes=5))
    rules = [
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.PUSH,
            minutes_before=5,
        )
    ]
    user = _build_user(user_id, rules=rules)

    calendar_entry_repo = create_calendar_entry_repo_double()
    _allow_calendar_entry_search(calendar_entry_repo, now.date(), entry)

    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    allow(push_notification_repo).search.and_return(
        [
            PushNotificationEntity(
                user_id=user_id,
                push_subscription_ids=[],
                content="{}",
                status="success",
                triggered_by="existing",
            )
        ]
    )

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo,
        push_notification_repo=push_notification_repo,
    )
    uow_factory = create_uow_factory_double(create_uow_double())

    recorder = _Recorder(commands=[])
    handler = CalendarEntryNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.send_push_notification_handler = recorder
    handler.sms_gateway = _SmsGateway()

    await handler.handle(CalendarEntryNotificationCommand(user=user))

    assert recorder.commands == []


@pytest.mark.asyncio
@freeze_time("2026-02-01 10:00:00")
async def test_calendar_entry_text_creates_message_and_sends_sms() -> None:
    user_id = uuid4()
    now = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
    entry = _build_entry(user_id, now + timedelta(minutes=10))
    rules = [
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.TEXT,
            minutes_before=10,
        )
    ]
    user = _build_user(user_id, rules=rules)

    calendar_entry_repo = create_calendar_entry_repo_double()
    _allow_calendar_entry_search(calendar_entry_repo, now.date(), entry)

    message_repo = create_repo_double(MessageRepositoryReadOnlyProtocol)
    allow(message_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo,
        message_repo=message_repo,
    )
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)
    sms_gateway = _SmsGateway()

    handler = CalendarEntryNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.send_push_notification_handler = _Recorder(commands=[])
    handler.sms_gateway = sms_gateway

    await handler.handle(CalendarEntryNotificationCommand(user=user))

    assert sms_gateway.sent
    assert uow.added
    message = uow.added[0]
    assert message.triggered_by is not None
    assert message.triggered_by.startswith("calendar_entry_reminder:")


@pytest.mark.asyncio
@freeze_time("2026-02-01 10:00:00")
async def test_calendar_entry_kiosk_alarm_emits_event_without_persisting() -> None:
    user_id = uuid4()
    now = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
    entry = _build_entry(user_id, now)
    rules = [
        value_objects.CalendarEntryNotificationRule(
            channel=value_objects.CalendarEntryNotificationChannel.KIOSK_ALARM,
            minutes_before=0,
        )
    ]
    user = _build_user(user_id, rules=rules)

    calendar_entry_repo = create_calendar_entry_repo_double()
    _allow_calendar_entry_search(calendar_entry_repo, now.date(), entry)

    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(now.date(), user_id, template)

    day_repo = create_day_repo_double()
    allow(day_repo).get.with_args(day.id).and_return(day)

    ro_repos = create_read_only_repos_double(
        calendar_entry_repo=calendar_entry_repo,
        day_repo=day_repo,
    )
    uow = create_uow_double(day_repo=day_repo)
    uow_factory = create_uow_factory_double(uow)

    handler = CalendarEntryNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.send_push_notification_handler = _Recorder(commands=[])
    handler.sms_gateway = _SmsGateway()

    await handler.handle(CalendarEntryNotificationCommand(user=user))

    assert uow.added
    updated_day = uow.added[0]
    assert updated_day.alarms == []

    events = updated_day.collect_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, AlarmTriggeredEvent)
    assert event.alarm_type == value_objects.AlarmType.KIOSK
    assert event.alarm_name == "Calendar reminder: Team Sync"

    expected_alarm_id = uuid5(
        NAMESPACE_DNS,
        f"{entry.id}:{entry.starts_at.isoformat()}:0:"
        f"{value_objects.CalendarEntryNotificationChannel.KIOSK_ALARM.value}",
    )
    assert event.alarm_id == expected_alarm_id
