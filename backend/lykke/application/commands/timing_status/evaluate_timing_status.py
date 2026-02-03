"""Command to emit timing status change events."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as dt_date, timedelta
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity, TaskEntity
from lykke.domain.events.timing_status_events import (
    RoutineTimingStatusChangedEvent,
    TaskTimingStatusChangedEvent,
)
from lykke.domain.services.timing_status import TimingStatusService


@dataclass(frozen=True)
class EvaluateTimingStatusCommand(Command):
    """Command to evaluate and emit timing status changes for today."""

    date: dt_date | None = None
    poll_interval_seconds: int = 60


class EvaluateTimingStatusHandler(
    BaseCommandHandler[EvaluateTimingStatusCommand, None]
):
    """Evaluates timing status changes and emits DomainEvents."""

    async def handle(self, command: EvaluateTimingStatusCommand) -> None:
        async with self.new_uow() as uow:
            try:
                user = self.user
                user_timezone = user.settings.timezone if user.settings else None
            except Exception:
                user_timezone = None

            now = get_current_datetime_in_timezone(user_timezone)
            previous_time = now - timedelta(seconds=command.poll_interval_seconds)
            target_date = command.date or get_current_date(user_timezone)

            tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(date=target_date)
            )
            routines = await uow.routine_ro_repo.search(
                value_objects.RoutineQuery(date=target_date)
            )
            tasks_by_routine_definition = self._group_tasks_by_routine_definition(tasks)

            updated_task_ids: set[UUID] = set()
            updated_routine_ids: set[UUID] = set()

            for task in tasks:
                current_status = TimingStatusService.task_status(
                    task, now, timezone=user_timezone
                )
                previous_status = TimingStatusService.task_status(
                    task, previous_time, timezone=user_timezone
                )

                if current_status.status == previous_status.status:
                    continue

                if task.id in updated_task_ids:
                    continue

                task_event = TaskTimingStatusChangedEvent(
                    user_id=self.user.id,
                    task_id=task.id,
                    old_timing_status=previous_status.status,
                    new_timing_status=current_status.status,
                    old_next_available_time=previous_status.next_available_time,
                    new_next_available_time=current_status.next_available_time,
                    task_scheduled_date=task.scheduled_date,
                    entity_id=task.id,
                    entity_type="task",
                    entity_date=task.scheduled_date,
                )
                task.add_event(task_event)
                uow.add(task)
                updated_task_ids.add(task.id)

            for routine in routines:
                routine_tasks = tasks_by_routine_definition.get(
                    routine.routine_definition_id, []
                )
                if not routine_tasks:
                    continue

                current_status = TimingStatusService.routine_status(
                    routine, routine_tasks, now, timezone=user_timezone
                )
                previous_status = TimingStatusService.routine_status(
                    routine, routine_tasks, previous_time, timezone=user_timezone
                )

                if current_status.status == previous_status.status:
                    continue

                if routine.id in updated_routine_ids:
                    continue

                routine_event = RoutineTimingStatusChangedEvent(
                    user_id=self.user.id,
                    routine_id=routine.id,
                    old_timing_status=previous_status.status,
                    new_timing_status=current_status.status,
                    old_next_available_time=previous_status.next_available_time,
                    new_next_available_time=current_status.next_available_time,
                    routine_date=routine.date,
                    entity_id=routine.id,
                    entity_type="routine",
                    entity_date=routine.date,
                )
                routine.add_event(routine_event)
                uow.add(routine)
                updated_routine_ids.add(routine.id)

    @staticmethod
    def _group_tasks_by_routine_definition(
        tasks: Iterable[TaskEntity],
    ) -> dict[UUID, list[TaskEntity]]:
        grouped: dict[UUID, list[TaskEntity]] = {}
        for task in tasks:
            if task.routine_definition_id is None:
                continue
            key = task.routine_definition_id
            grouped.setdefault(key, []).append(task)
        return grouped
