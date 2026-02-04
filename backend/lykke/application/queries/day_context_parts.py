"""Query handlers for loading individual DayContext parts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as datetime_date, datetime, time, timedelta

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    BrainDumpRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
    RoutineDefinitionRepositoryReadOnlyProtocol,
    RoutineRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.core.constants import DEFAULT_END_OF_DAY_TIME
from lykke.domain import value_objects
from lykke.domain.entities import (
    BrainDumpEntity,
    CalendarEntryEntity,
    DayEntity,
    MessageEntity,
    PushNotificationEntity,
    RoutineEntity,
    TaskEntity,
)


@dataclass(frozen=True)
class GetDayEntityQuery(Query):
    """Query to get the Day entity for a date."""

    date: datetime_date


class GetDayEntityHandler(BaseQueryHandler[GetDayEntityQuery, DayEntity]):
    """Loads the Day entity for a given date."""

    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayEntityQuery) -> DayEntity:
        """Handle day lookup query."""
        day_id = DayEntity.id_from_date_and_user(query.date, self.user.id)
        return await self.day_ro_repo.get(day_id)


@dataclass(frozen=True)
class GetDayTasksQuery(Query):
    """Query to get tasks for a date."""

    date: datetime_date


class GetDayTasksHandler(BaseQueryHandler[GetDayTasksQuery, list[TaskEntity]]):
    """Loads tasks for a given date."""

    task_ro_repo: TaskRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayTasksQuery) -> list[TaskEntity]:
        """Handle tasks lookup query."""
        return await self.get_tasks(query.date)

    async def get_tasks(self, date: datetime_date) -> list[TaskEntity]:
        """Load tasks for a given date."""
        tasks = await self.task_ro_repo.search(value_objects.TaskQuery(date=date))
        return sorted(
            tasks,
            key=lambda task: (
                task.time_window.start_time
                if task.time_window and task.time_window.start_time
                else task.time_window.available_time
                if task.time_window and task.time_window.available_time
                else DEFAULT_END_OF_DAY_TIME
            ),
        )


@dataclass(frozen=True)
class GetDayCalendarEntriesQuery(Query):
    """Query to get calendar entries for a date."""

    date: datetime_date


class GetDayCalendarEntriesHandler(
    BaseQueryHandler[GetDayCalendarEntriesQuery, list[CalendarEntryEntity]]
):
    """Loads calendar entries for a given date."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetDayCalendarEntriesQuery
    ) -> list[CalendarEntryEntity]:
        """Handle calendar entries lookup query."""
        entries = await self.calendar_entry_ro_repo.search(
            value_objects.CalendarEntryQuery(date=query.date)
        )
        return sorted(entries, key=lambda entry: entry.starts_at)


@dataclass(frozen=True)
class GetDayRoutinesQuery(Query):
    """Query to get routines for a date."""

    date: datetime_date


class GetDayRoutinesHandler(BaseQueryHandler[GetDayRoutinesQuery, list[RoutineEntity]]):
    """Loads routines for a given date."""

    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayRoutinesQuery) -> list[RoutineEntity]:
        """Handle routines lookup query."""
        return await self.get_routines(query.date)

    async def get_routines(
        self, date: datetime_date, *, tasks: list[TaskEntity] | None = None
    ) -> list[RoutineEntity]:
        """Load routines for a given date."""
        routines = await self.routine_ro_repo.search(
            value_objects.RoutineQuery(date=date)
        )
        if not routines:
            if tasks is None:
                tasks = await self.task_ro_repo.search(
                    value_objects.TaskQuery(date=date)
                )
            routines = await self._build_routines_from_tasks(date, tasks)
        return sorted(routines, key=lambda routine: getattr(routine, "name", ""))

    async def _build_routines_from_tasks(
        self, date: datetime_date, tasks: list[TaskEntity]
    ) -> list[RoutineEntity]:
        routine_definition_ids = {
            task.routine_definition_id
            for task in tasks
            if task.routine_definition_id is not None
        }
        if not routine_definition_ids:
            return []

        routine_definitions = await self.routine_definition_ro_repo.all()
        routines: list[RoutineEntity] = []
        for routine_definition in routine_definitions:
            if routine_definition.id in routine_definition_ids:
                routines.append(
                    RoutineEntity.from_definition(
                        routine_definition, date, self.user.id
                    )
                )
        return routines


@dataclass(frozen=True)
class GetDayBrainDumpsQuery(Query):
    """Query to get brain dump items for a date."""

    date: datetime_date


class GetDayBrainDumpsHandler(
    BaseQueryHandler[GetDayBrainDumpsQuery, list[BrainDumpEntity]]
):
    """Loads brain dumps for a given date."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayBrainDumpsQuery) -> list[BrainDumpEntity]:
        """Handle brain dumps lookup query."""
        items = await self.brain_dump_ro_repo.search(
            value_objects.BrainDumpQuery(date=query.date)
        )
        return sorted(items, key=lambda item: item.created_at)


@dataclass(frozen=True)
class GetDayPushNotificationsQuery(Query):
    """Query to get push notifications for a date."""

    date: datetime_date


class GetDayPushNotificationsHandler(
    BaseQueryHandler[GetDayPushNotificationsQuery, list[PushNotificationEntity]]
):
    """Loads push notifications for a given date."""

    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetDayPushNotificationsQuery
    ) -> list[PushNotificationEntity]:
        """Handle push notifications lookup query."""
        start_of_day = datetime.combine(query.date, time.min, tzinfo=UTC)
        end_of_day = start_of_day + timedelta(days=1)
        notifications = await self.push_notification_ro_repo.search(
            value_objects.PushNotificationQuery(
                sent_after=start_of_day,
                sent_before=end_of_day,
                order_by="sent_at",
                order_by_desc=True,
            )
        )
        return sorted(
            notifications, key=lambda notification: notification.sent_at, reverse=True
        )


@dataclass(frozen=True)
class GetDayMessagesQuery(Query):
    """Query to get messages for a date."""

    date: datetime_date


class GetDayMessagesHandler(BaseQueryHandler[GetDayMessagesQuery, list[MessageEntity]]):
    """Loads messages for a given date."""

    message_ro_repo: MessageRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayMessagesQuery) -> list[MessageEntity]:
        """Handle messages lookup query."""
        start_of_day = datetime.combine(query.date, time.min, tzinfo=UTC)
        end_of_day = start_of_day + timedelta(days=1)
        messages = await self.message_ro_repo.search(
            value_objects.MessageQuery(
                created_after=start_of_day,
                created_before=end_of_day,
                order_by="created_at",
                order_by_desc=False,
            )
        )
        return sorted(messages, key=lambda message: message.created_at)
