"""Query to get the complete context for a day."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, date as datetime_date, datetime, time, timedelta
from typing import cast

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    BrainDumpRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
    RoutineDefinitionRepositoryReadOnlyProtocol,
    RoutineRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.core.constants import DEFAULT_END_OF_DAY_TIME
from lykke.core.exceptions import NotFoundError
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
class GetDayContextQuery(Query):
    """Query to get day context."""

    date: datetime_date


class GetDayContextHandler(
    BaseQueryHandler[GetDayContextQuery, value_objects.DayContext]
):
    """Gets the complete context for a day."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayContextQuery) -> value_objects.DayContext:
        """Handle get day context query."""
        return await self.get_day_context(query.date)

    async def get_day_context(self, date: datetime_date) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            date: The date to get context for

        Returns:
            A DayContext with all related data
        """
        day_id = DayEntity.id_from_date_and_user(date, self.user.id)

        start_of_day = datetime.combine(date, time.min, tzinfo=UTC)
        end_of_day = start_of_day + timedelta(days=1)

        (
            tasks_result,
            calendar_entries_result,
            routines_result,
            day_result,
            brain_dumps_result,
            push_notifications_result,
            messages_result,
        ) = await asyncio.gather(
            self.task_ro_repo.search(value_objects.TaskQuery(date=date)),
            self.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(date=date)
            ),
            self.routine_ro_repo.search(value_objects.RoutineQuery(date=date)),
            self.day_ro_repo.get(day_id),
            self.brain_dump_ro_repo.search(value_objects.BrainDumpQuery(date=date)),
            self.push_notification_ro_repo.search(
                value_objects.PushNotificationQuery(
                    sent_after=start_of_day,
                    sent_before=end_of_day,
                    order_by="sent_at",
                    order_by_desc=True,
                )
            ),
            self.message_ro_repo.search(
                value_objects.MessageQuery(
                    created_after=start_of_day,
                    created_before=end_of_day,
                    order_by="created_at",
                    order_by_desc=False,
                )
            ),
            return_exceptions=True,
        )

        tasks = cast(
            "list[TaskEntity]", self._unwrap_result(tasks_result, "tasks result")
        )
        calendar_entries = cast(
            "list[CalendarEntryEntity]",
            self._unwrap_result(calendar_entries_result, "calendar entries result"),
        )
        routines = cast(
            "list[RoutineEntity]",
            self._unwrap_result(routines_result, "routines result"),
        )
        brain_dumps = cast(
            "list[BrainDumpEntity]",
            self._unwrap_result(brain_dumps_result, "brain dumps result"),
        )
        push_notifications = cast(
            "list[PushNotificationEntity]",
            self._unwrap_result(push_notifications_result, "push notifications result"),
        )
        messages = cast(
            "list[MessageEntity]",
            self._unwrap_result(messages_result, "messages result"),
        )

        if isinstance(day_result, NotFoundError):
            raise day_result
        elif isinstance(day_result, Exception):
            # Propagate other errors to maintain existing error handling behaviour
            raise day_result
        else:
            if not isinstance(day_result, DayEntity):
                raise TypeError(
                    f"Unexpected day result type: {type(day_result).__name__}"
                )
            day = day_result

        if not routines:
            routines = await self._build_routines_from_tasks(date, tasks)

        return self._build_context(
            day,
            tasks,
            calendar_entries,
            routines,
            brain_dumps,
            push_notifications,
            messages,
        )

    @staticmethod
    def _unwrap_result(result: object, name: str) -> object:
        """Raise any exception returned by asyncio.gather."""
        if isinstance(result, Exception):
            raise type(result)(f"{name}: {result}") from result
        return result

    def _build_context(
        self,
        day: DayEntity,
        tasks: list[TaskEntity],
        calendar_entries: list[CalendarEntryEntity],
        routines: list[RoutineEntity],
        brain_dumps: list[BrainDumpEntity],
        push_notifications: list[PushNotificationEntity],
        messages: list[MessageEntity],
    ) -> value_objects.DayContext:
        """Build a DayContext from loaded data.

        Args:
            day: The day entity
            tasks: List of tasks for the day
            calendar_entries: List of calendar entries for the day

        Returns:
            A DayContext with sorted tasks and calendar entries
        """
        return value_objects.DayContext(
            day=day,
            tasks=sorted(
                tasks,
                key=lambda x: (
                    x.time_window.start_time
                    if x.time_window and x.time_window.start_time
                    else x.time_window.available_time
                    if x.time_window and x.time_window.available_time
                    else DEFAULT_END_OF_DAY_TIME
                ),
            ),
            calendar_entries=sorted(calendar_entries, key=lambda e: e.starts_at),
            routines=sorted(
                routines,
                key=lambda r: getattr(r, "name", ""),
            ),
            brain_dumps=sorted(
                brain_dumps,
                key=lambda item: item.created_at,
            ),
            push_notifications=sorted(
                push_notifications,
                key=lambda notification: notification.sent_at,
                reverse=True,
            ),
            messages=sorted(
                messages,
                key=lambda message: message.created_at,
            ),
        )

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
