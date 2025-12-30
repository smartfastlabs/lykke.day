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
    user_uuid: UUID
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
        user_uuid: UUID,
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
        self.user_uuid = user_uuid
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
                        routine_task.task_definition_uuid,
                    )
                    task = objects.Task(
                        user_uuid=self.user_uuid,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_uuid=routine.uuid,
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
        template_uuid: UUID | None = None,
    ) -> DayContext:
        if template_uuid is None:
            with suppress(exceptions.NotFoundError):
                day_uuid = objects.Day.uuid_from_date_and_user(date, self.user_uuid)
                existing_day = await self.day_repo.get(day_uuid)
                template_uuid = existing_day.template_uuid

        # template_uuid will be None here, so base_day will look up by slug from template_defaults
        result: DayContext = DayContext(
            day=await DayService.base_day(
                date,
                user_uuid=self.user_uuid,
                template_uuid=template_uuid,
                day_template_repo=self.day_template_repo,
                user_repo=self.user_repo,
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
            routine_tasks = [t for t in tasks if t.routine_uuid is not None]
            if routine_tasks:
                await asyncio.gather(
                    *[self.task_repo.delete(task) for task in routine_tasks]
                )
            day = await DayService.get_or_create(
                date,
                user_uuid=self.user_uuid,
                day_repo=self.day_repo,
                day_template_repo=self.day_template_repo,
                user_repo=self.user_repo,
            )
            day.status = objects.DayStatus.UNSCHEDULED
            await self.day_repo.put(day)

    async def schedule(
        self,
        date: datetime.date,
        template_uuid: UUID | None = None,
    ) -> objects.DayContext:
        async with self.transaction():
            await self.task_repo.delete_many(DateQuery(date=date))

            result: objects.DayContext = await self.preview(
                date,
                template_uuid=template_uuid,
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
        if isinstance(obj, Task):
            if action.type in [TaskStatus.COMPLETE, TaskStatus.PUNT]:
                obj.status = TaskStatus(action.type)
            await self.task_repo.put(obj)

        elif isinstance(obj, Event):
            await self.event_repo.put(obj)
        else:
            raise ValueError(f"Invalid object type: {type(obj)}")
        return obj
