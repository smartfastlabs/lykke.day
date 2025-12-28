import asyncio
import datetime
from contextlib import suppress
from typing import Protocol, TypeVar

from loguru import logger

from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.entities import (
    Action,
    ActionType,
    DayContext,
    DayTemplate,
    Event,
    Task,
    TaskStatus,
)
from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.infrastructure.utils.user_settings import load_user_settings
from planned.infrastructure.utils.dates import get_current_date

from .base import BaseService
from .day import DayService


def is_routine_active(schedule: objects.RoutineSchedule, date: datetime.date) -> bool:
    if not schedule.weekdays:
        return True
    return date.weekday() in schedule.weekdays


class Actionable(Protocol):
    actions: list[Action]


HasActionsType = TypeVar("HasActionsType", bound=Actionable)


class PlanningService(BaseService):
    day_repo: DayRepositoryProtocol
    day_template_repo: DayTemplateRepositoryProtocol
    event_repo: EventRepositoryProtocol
    message_repo: MessageRepositoryProtocol
    routine_repo: RoutineRepositoryProtocol
    task_definition_repo: TaskDefinitionRepositoryProtocol
    task_repo: TaskRepositoryProtocol
    day_service: DayService | None

    def __init__(
        self,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        routine_repo: RoutineRepositoryProtocol,
        task_definition_repo: TaskDefinitionRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        day_service: DayService | None = None,
    ) -> None:
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.event_repo = event_repo
        self.message_repo = message_repo
        self.routine_repo = routine_repo
        self.task_definition_repo = task_definition_repo
        self.task_repo = task_repo
        self.day_service = day_service


    async def preview_tasks(self, date: datetime.date) -> list[Task]:
        result: list[Task] = []
        for routine in await self.routine_repo.all():
            logger.info(routine)
            if is_routine_active(routine.routine_schedule, date):
                for routine_task in routine.tasks:
                    task = objects.Task(
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        task_definition=await self.task_definition_repo.get(
                            routine_task.task_definition_id,
                        ),
                        schedule=routine_task.schedule,
                        scheduled_date=date,
                        status=TaskStatus.NOT_STARTED,
                        category=routine.category,
                    )
                    result.append(task)

        return result

    async def preview(
        self,
        date: datetime.date,
        template_id: str | None = None,
    ) -> DayContext:
        if template_id is None:
            with suppress(exceptions.NotFoundError):
                existing_day = await self.day_repo.get(str(date))
                template_id = existing_day.template_id

        if template_id is None:
            user_settings = load_user_settings()
            template_id = user_settings.template_defaults[date.weekday()]

        result: DayContext = DayContext(
            day=await DayService.base_day(
                date,
                template_id=template_id,
                day_template_repo=self.day_template_repo,
            ),
        )
        result.tasks, result.events, result.messages = await asyncio.gather(
            self.preview_tasks(date),
            self.event_repo.search(date),
            self.message_repo.search(date),
        )

        return result

    async def unschedule(self, date: datetime.date) -> None:
        await self.task_repo.delete_by_date(
            date,
            lambda t: t.routine_id is not None,
        )
        day = await DayService.get_or_create(
            date,
            day_repo=self.day_repo,
            day_template_repo=self.day_template_repo,
        )
        day.status = objects.DayStatus.UNSCHEDULED
        await self.day_repo.put(day)

    async def schedule(
        self,
        date: datetime.date,
        template_id: str | None = None,
    ) -> objects.DayContext:
        await self.task_repo.delete_by_date(date)

        result: objects.DayContext = await self.preview(
            date,
            template_id=template_id,
        )
        result.day.status = objects.DayStatus.SCHEDULED
        await asyncio.gather(
            self.day_repo.put(result.day),
            *[self.task_repo.put(task) for task in result.tasks],
        )

        return result

    async def save_action(
        self,
        obj: HasActionsType,
        action: Action,
    ) -> HasActionsType:
        obj.actions.append(action)
        action_type: TaskStatus = TaskStatus(action.type)
        if isinstance(obj, Task):
            if action_type in [TaskStatus.COMPLETE, TaskStatus.PUNTED]:
                obj.status = action_type
            await self.task_repo.put(obj)

        elif isinstance(obj, Event):
            await self.event_repo.put(obj)
        else:
            raise ValueError(f"Invalid object type: {type(obj)}")
        return obj
