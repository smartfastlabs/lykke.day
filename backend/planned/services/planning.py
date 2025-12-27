import asyncio
import datetime
from contextlib import suppress
from typing import Protocol, TypeVar

from loguru import logger

from planned import exceptions, objects
from planned.objects import (
    Action,
    ActionType,
    DayContext,
    DayTemplate,
    Event,
    Task,
    TaskStatus,
)
from planned.objects.user_settings import user_settings
from planned.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)
from planned.utils.dates import get_current_date

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
    day_repo: DayRepository
    day_template_repo: DayTemplateRepository
    event_repo: EventRepository
    message_repo: MessageRepository
    routine_repo: RoutineRepository
    task_definition_repo: TaskDefinitionRepository
    task_repo: TaskRepository
    day_service: DayService | None

    def __init__(
        self,
        day_repo: DayRepository,
        day_template_repo: DayTemplateRepository,
        event_repo: EventRepository,
        message_repo: MessageRepository,
        routine_repo: RoutineRepository,
        task_definition_repo: TaskDefinitionRepository,
        task_repo: TaskRepository,
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

    @classmethod
    def new(
        cls,
        day_repo: DayRepository | None = None,
        day_template_repo: DayTemplateRepository | None = None,
        event_repo: EventRepository | None = None,
        message_repo: MessageRepository | None = None,
        routine_repo: RoutineRepository | None = None,
        task_definition_repo: TaskDefinitionRepository | None = None,
        task_repo: TaskRepository | None = None,
        day_service: DayService | None = None,
    ) -> "PlanningService":
        """Create a new instance of PlanningService with optional repositories."""
        if day_repo is None:
            day_repo = DayRepository()
        if day_template_repo is None:
            day_template_repo = DayTemplateRepository()
        if event_repo is None:
            event_repo = EventRepository()
        if message_repo is None:
            message_repo = MessageRepository()
        if routine_repo is None:
            routine_repo = RoutineRepository()
        if task_definition_repo is None:
            task_definition_repo = TaskDefinitionRepository()
        if task_repo is None:
            task_repo = TaskRepository()
        return cls(
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            routine_repo=routine_repo,
            task_definition_repo=task_definition_repo,
            task_repo=task_repo,
            day_service=day_service,
        )

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
