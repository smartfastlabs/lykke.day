"""Command to evaluate deterministic calendar entry reminders."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_DNS, UUID, uuid5

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.notifications import (
    build_notification_payload_for_calendar_entry_reminder,
    format_calendar_entry_time,
    format_calendar_entry_when,
    pick_calendar_entry_message_template,
)
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.application.utils.filters import filter_upcoming_calendar_entries
from lykke.core.utils.dates import (
    get_current_date,
    get_current_datetime,
    get_tomorrows_date,
    resolve_timezone,
)
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import (
    CalendarEntryEntity,
    DayEntity,
    MessageEntity,
    PushNotificationEntity,
    UserEntity,
)
from lykke.domain.events.ai_chat_events import MessageSentEvent

EVALUATION_WINDOW = timedelta(minutes=1)


@dataclass(frozen=True)
class CalendarEntryNotificationCommand(Command):
    """Command to evaluate calendar entry reminders for a user."""

    user_id: UUID
    triggered_by: str | None = None


class CalendarEntryNotificationHandler(
    BaseCommandHandler[CalendarEntryNotificationCommand, None]
):
    """Deterministically sends calendar entry reminders."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        send_push_notification_handler: SendPushNotificationHandler,
        sms_gateway: SMSProviderProtocol,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._send_push_notification_handler = send_push_notification_handler
        self._sms_gateway = sms_gateway

    async def handle(self, command: CalendarEntryNotificationCommand) -> None:
        _ = command.triggered_by
        user = await self.user_ro_repo.get(self.user_id)
        settings = user.settings.calendar_entry_notification_settings
        if not settings.enabled or not settings.rules:
            return

        rules = [
            rule
            for rule in settings.rules
            if isinstance(rule, value_objects.CalendarEntryNotificationRule)
        ]
        if not rules:
            return

        max_minutes = max(rule.minutes_before for rule in rules)
        look_ahead = timedelta(minutes=max_minutes) + EVALUATION_WINDOW
        entries = await self._load_calendar_entries(user, look_ahead)
        upcoming = filter_upcoming_calendar_entries(entries, look_ahead)
        now = get_current_datetime()

        for entry in upcoming:
            await self._maybe_send_for_entry(entry, rules, user, now)

    async def _load_calendar_entries(
        self,
        user: UserEntity,
        look_ahead: timedelta,
    ) -> list[CalendarEntryEntity]:
        _ = look_ahead
        timezone = user.settings.timezone
        dates = {get_current_date(timezone), get_tomorrows_date(timezone)}
        entries: list[CalendarEntryEntity] = []
        for day_date in dates:
            entries.extend(
                await self.calendar_entry_ro_repo.search(
                    value_objects.CalendarEntryQuery(date=day_date)
                )
            )
        return entries

    async def _maybe_send_for_entry(
        self,
        entry: CalendarEntryEntity,
        rules: list[value_objects.CalendarEntryNotificationRule],
        user: UserEntity,
        now: datetime,
    ) -> None:
        for rule in rules:
            scheduled_for = entry.starts_at - timedelta(minutes=rule.minutes_before)
            if not self._within_window(now, scheduled_for):
                continue
            triggered_by = self._build_triggered_by(entry, rule)
            await self._handle_rule(entry, rule, user, scheduled_for, triggered_by)

    async def _handle_rule(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
        user: UserEntity,
        scheduled_for: datetime,
        triggered_by: str,
    ) -> None:
        if rule.channel == value_objects.CalendarEntryNotificationChannel.PUSH:
            await self._send_push(entry, rule, user, scheduled_for, triggered_by)
            return
        if rule.channel == value_objects.CalendarEntryNotificationChannel.TEXT:
            await self._send_text(entry, rule, user, scheduled_for, triggered_by)
            return
        if rule.channel == value_objects.CalendarEntryNotificationChannel.KIOSK_ALARM:
            await self._send_kiosk_alarm(entry, rule, user, scheduled_for, triggered_by)

    async def _send_push(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
        user: UserEntity,
        scheduled_for: datetime,
        triggered_by: str,
    ) -> None:
        if await self._has_recent_push(triggered_by, scheduled_for):
            return

        message = self._build_message(entry, rule, user.settings.timezone, triggered_by)
        payload = build_notification_payload_for_calendar_entry_reminder(
            entry,
            message,
            minutes_before=rule.minutes_before,
            scheduled_for=scheduled_for,
        )
        message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()

        subscriptions = await self.push_subscription_ro_repo.all()
        if not subscriptions:
            await self._record_skipped_push(
                payload=payload,
                message=message,
                message_hash=message_hash,
                triggered_by=triggered_by,
            )
            return

        await self._send_push_notification_handler.handle(
            SendPushNotificationCommand(
                subscriptions=subscriptions,
                content=payload,
                message=message,
                message_hash=message_hash,
                triggered_by=triggered_by,
            )
        )

    async def _record_skipped_push(
        self,
        *,
        payload: value_objects.NotificationPayload,
        message: str,
        message_hash: str,
        triggered_by: str,
    ) -> None:
        content_dict = dataclass_to_json_dict(payload)
        filtered_content = {k: v for k, v in content_dict.items() if v is not None}
        content_str = json.dumps(filtered_content)
        async with self.new_uow() as uow:
            notification = PushNotificationEntity(
                user_id=self.user_id,
                push_subscription_ids=[],
                content=content_str,
                status="skipped",
                error_message="no_subscriptions",
                message=message,
                message_hash=message_hash,
                triggered_by=triggered_by,
            )
            await uow.create(notification)

    async def _send_text(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
        user: UserEntity,
        scheduled_for: datetime,
        triggered_by: str,
    ) -> None:
        if not user.phone_number:
            return
        if await self._has_recent_message(triggered_by, scheduled_for):
            return

        message = self._build_message(entry, rule, user.settings.timezone, triggered_by)
        outgoing = MessageEntity(
            user_id=self.user_id,
            role=value_objects.MessageRole.ASSISTANT,
            type=value_objects.MessageType.SMS_OUTBOUND,
            content=message,
            meta={
                "provider": "twilio",
                "to_number": user.phone_number,
                "calendar_entry_id": str(entry.id),
                "scheduled_for": scheduled_for.isoformat(),
            },
            triggered_by=triggered_by,
        )
        outgoing.create()
        outgoing.add_event(
            MessageSentEvent(
                user_id=self.user_id,
                message_id=outgoing.id,
                role=outgoing.role.value,
                content_preview=outgoing.get_content_preview(),
            )
        )
        async with self.new_uow() as uow:
            uow.add(outgoing)

        try:
            await self._sms_gateway.send_message(user.phone_number, message)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed sending calendar reminder SMS: %s", exc)

    async def _send_kiosk_alarm(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
        user: UserEntity,
        scheduled_for: datetime,
        triggered_by: str,
    ) -> None:
        timezone = resolve_timezone(user.settings.timezone)
        local_dt = scheduled_for.astimezone(timezone)
        alarm_id = uuid5(
            NAMESPACE_DNS,
            f"{entry.id}:{entry.starts_at.isoformat()}:{rule.minutes_before}:{rule.channel.value}",
        )

        day_id = DayEntity.id_from_date_and_user(local_dt.date(), self.user_id)
        try:
            day = await self.day_ro_repo.get(day_id)
        except Exception:  # pylint: disable=broad-except
            logger.debug("Skipping kiosk alarm; day not found for %s", local_dt.date())
            return

        if any(alarm.id == alarm_id for alarm in day.alarms):
            return

        alarm = value_objects.Alarm(
            id=alarm_id,
            name=f"Calendar reminder: {entry.name}",
            time=local_dt.time(),
            datetime=local_dt.astimezone(UTC),
            type=value_objects.AlarmType.GENERIC,
            url="",
        )
        day.add_alarm(alarm)
        async with self.new_uow() as uow:
            uow.add(day)

    async def _has_recent_push(self, triggered_by: str, scheduled_for: datetime) -> bool:
        window_start = scheduled_for - EVALUATION_WINDOW
        existing = await self.push_notification_ro_repo.search(
            value_objects.PushNotificationQuery(
                triggered_by=triggered_by,
                sent_after=window_start,
            )
        )
        return bool(existing)

    async def _has_recent_message(
        self, triggered_by: str, scheduled_for: datetime
    ) -> bool:
        window_start = scheduled_for - EVALUATION_WINDOW
        existing = await self.message_ro_repo.search(
            value_objects.MessageQuery(
                triggered_by=triggered_by,
                created_after=window_start,
            )
        )
        return bool(existing)

    @staticmethod
    def _within_window(now: datetime, target: datetime) -> bool:
        return target <= now < target + EVALUATION_WINDOW

    def _build_triggered_by(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
    ) -> str:
        return (
            f"calendar_entry_reminder:{entry.id}:{entry.starts_at.isoformat()}:"
            f"{rule.channel.value}:{rule.minutes_before}"
        )

    def _build_message(
        self,
        entry: CalendarEntryEntity,
        rule: value_objects.CalendarEntryNotificationRule,
        timezone: str | None,
        triggered_by: str,
    ) -> str:
        local_time = format_calendar_entry_time(entry, timezone)
        when = format_calendar_entry_when(rule.minutes_before)
        template = pick_calendar_entry_message_template(rule.channel, triggered_by)
        return template.format(title=entry.name, time=local_time, when=when)
