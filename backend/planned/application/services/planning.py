import asyncio
import datetime
from contextlib import suppress
from typing import Protocol, TypeVar
from uuid import UUID

from loguru import logger

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.entities import Action, DayContext, Event, Task, TaskStatus
from planned.domain.value_objects.query import DateQuery

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
    user_id: UUID
    user_repo: UserRepositoryProtocol
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
        user: objects.User,
        user_repo: UserRepositoryProtocol,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        routine_repo: RoutineRepositoryProtocol,
        task_definition_repo: TaskDefinitionRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        day_service: DayService | None = None,
    ) -> None:
        super().__init__(user)
        self.user_id = user.id
        self.user_repo = user_repo
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
                    task_def = await self.task_definition_repo.get(
                        routine_task.task_definition_id,
                    )
                    task = objects.Task(
                        user_id=self.user_id,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        task_definition=task_def,
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
        template_id: UUID | None = None,
    ) -> DayContext:
        # Get template: either by id, from existing day, or from user defaults
        template: objects.DayTemplate
        if template_id is not None:
            template = await self.day_template_repo.get(template_id)
        else:
            # Try to get it from existing day
            template_found = False
            with suppress(exceptions.NotFoundError):
                day_id = objects.Day.id_from_date_and_user(date, self.user_id)
                existing_day = await self.day_repo.get(day_id)
                if existing_day.template:
                    template = existing_day.template
                    template_found = True
            if not template_found:
                # Get from user's template_defaults
                user = await self.user_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await self.day_template_repo.get_by_slug(template_slug)

        result: DayContext = DayContext(
            day=await DayService.base_day(
                date,
                user_id=self.user_id,
                template=template,
            ),
        )

        result.tasks, result.events, result.messages = await asyncio.gather(
            self.preview_tasks(date),
            self.event_repo.search_query(DateQuery(date=date)),
            self.message_repo.search_query(DateQuery(date=date)),
        )

        return result

    async def unschedule(self, date: datetime.date) -> None:
        async with self.transaction():
            # Get all tasks for the date, filter for routine tasks, then delete them
            tasks = await self.task_repo.search_query(DateQuery(date=date))
            routine_tasks = [t for t in tasks if t.routine_id is not None]
            if routine_tasks:
                await asyncio.gather(
                    *[self.task_repo.delete(task) for task in routine_tasks]
                )
            # Create a DayService instance to use get_or_create
            # Load context first to create the service
            ctx = await DayService.load_context_cls(
                date,
                user_id=self.user_id,
                day_repo=self.day_repo,
                day_template_repo=self.day_template_repo,
                event_repo=self.event_repo,
                message_repo=self.message_repo,
                task_repo=self.task_repo,
                user_repo=self.user_repo,
            )
            day_svc = DayService(
                user=self.user,
                ctx=ctx,
                day_repo=self.day_repo,
                day_template_repo=self.day_template_repo,
                event_repo=self.event_repo,
                message_repo=self.message_repo,
                task_repo=self.task_repo,
            )
            user = await self.user_repo.get(self.user_id)
            day = await day_svc.get_or_create(
                date,
                user=user,
                user_repo=self.user_repo,
            )
            day.status = objects.DayStatus.UNSCHEDULED
            await self.day_repo.put(day)

    async def schedule(
        self,
        date: datetime.date,
        template_id: UUID | None = None,
    ) -> objects.DayContext:
        async with self.transaction():
            await self.task_repo.delete_many(DateQuery(date=date))

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
        from planned.domain.value_objects.action import ActionType

        if isinstance(obj, Task):
            obj.actions.append(action)
            if action.type in [ActionType.COMPLETE, ActionType.PUNT]:
                obj.status = TaskStatus(action.type.value)
            await self.task_repo.put(obj)

        elif isinstance(obj, Event):
            obj.actions.append(action)
            await self.event_repo.put(obj)
        else:
            raise ValueError(f"Invalid object type: {type(obj)}")
        return obj
