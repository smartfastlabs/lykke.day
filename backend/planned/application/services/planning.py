import asyncio
import datetime
from typing import Protocol, TypeVar
from uuid import UUID

from loguru import logger

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.entities import Action, DayContext, Event, Task, TaskStatus
from planned.domain.value_objects.query import DateQuery

from .base import BaseService


def is_routine_active(schedule: objects.RoutineSchedule, date: datetime.date) -> bool:
    if not schedule.weekdays:
        return True
    return date.weekday() in schedule.weekdays


class Actionable(Protocol):
    actions: list[Action]


HasActionsType = TypeVar("HasActionsType", bound=Actionable)


class PlanningService(BaseService):
    """Service for planning and scheduling days."""

    user_id: UUID
    uow_factory: UnitOfWorkFactory

    def __init__(
        self,
        user: objects.User,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        """Initialize PlanningService.

        Args:
            user: The user for whom to plan
            uow_factory: Factory for creating UnitOfWork instances
        """
        super().__init__(user)
        self.user_id = user.id
        self.uow_factory = uow_factory

    async def preview_tasks(self, date: datetime.date) -> list[Task]:
        """Preview tasks that would be created for a given date.

        Args:
            date: The date to preview tasks for

        Returns:
            List of tasks that would be created
        """
        uow = self.uow_factory.create(self.user_id)
        async with uow:
            result: list[Task] = []
            for routine in await uow.routines.all():
                logger.info(routine)
                if is_routine_active(routine.routine_schedule, date):
                    for routine_task in routine.tasks:
                        task_def = await uow.task_definitions.get(
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
        """Preview what a day would look like if scheduled.

        Args:
            date: The date to preview
            template_id: Optional template ID to use (otherwise uses defaults)

        Returns:
            A DayContext with preview data (not saved)
        """
        uow = self.uow_factory.create(self.user_id)
        async with uow:
            # Get template: either by id, from existing day, or from user defaults
            template: objects.DayTemplate
            if template_id is not None:
                template = await uow.day_templates.get(template_id)
            else:
                # Try to get it from existing day
                template_found = False
                try:
                    day_id = objects.Day.id_from_date_and_user(date, self.user_id)
                    existing_day = await uow.days.get(day_id)
                    if existing_day.template:
                        template = existing_day.template
                        template_found = True
                except exceptions.NotFoundError:
                    # Day doesn't exist, will use default template
                    pass

                if not template_found:
                    # Get from user's template_defaults
                    user = await uow.users.get(self.user_id)
                    template_slug = user.settings.template_defaults[date.weekday()]
                    template = await uow.day_templates.get_by_slug(template_slug)

            result: DayContext = DayContext(
                day=objects.Day.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                ),
            )

            result.tasks, result.events, result.messages = await asyncio.gather(
                self.preview_tasks(date),
                uow.events.search_query(DateQuery(date=date)),
                uow.messages.search_query(DateQuery(date=date)),
            )

            return result

    async def unschedule(self, date: datetime.date) -> None:
        """Unschedule a day, removing routine tasks and marking day as unscheduled.

        Args:
            date: The date to unschedule
        """
        uow = self.uow_factory.create(self.user_id)
        async with uow:
            # Get all tasks for the date, filter for routine tasks, then delete them
            tasks = await uow.tasks.search_query(DateQuery(date=date))
            routine_tasks = [t for t in tasks if t.routine_id is not None]
            if routine_tasks:
                await asyncio.gather(
                    *[uow.tasks.delete(task) for task in routine_tasks]
                )

            # Get or create the day
            day_id = objects.Day.id_from_date_and_user(date, self.user_id)
            try:
                day = await uow.days.get(day_id)
            except exceptions.NotFoundError:
                # Day doesn't exist, create it
                user = await uow.users.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = objects.Day.create_for_date(
                    date, user_id=self.user_id, template=template
                )

            # Unschedule the day using domain method
            day.unschedule()
            await uow.days.put(day)
            await uow.commit()

    async def schedule(
        self,
        date: datetime.date,
        template_id: UUID | None = None,
    ) -> objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            date: The date to schedule
            template_id: Optional template ID to use (otherwise uses defaults)

        Returns:
            A DayContext with the scheduled day and tasks
        """
        uow = self.uow_factory.create(self.user_id)
        async with uow:
            # Delete existing tasks for this date
            await uow.tasks.delete_many(DateQuery(date=date))

            # Get preview of what the day would look like
            # Note: preview creates its own UoW, so we need to recreate entities here
            preview_result = await self.preview(date, template_id=template_id)

            # Get the day from preview and schedule it
            if preview_result.day.template is None:
                raise ValueError("Day template is required to schedule")

            # Re-fetch template to ensure it's in the current UoW context
            template = await uow.day_templates.get(preview_result.day.template.id)
            day = objects.Day.create_for_date(
                date, user_id=self.user_id, template=template
            )
            day.schedule(template)

            # Create tasks from preview
            tasks = preview_result.tasks

            # Save day and tasks
            await asyncio.gather(
                uow.days.put(day),
                *[uow.tasks.put(task) for task in tasks],
            )
            await uow.commit()

            # Return context with saved day
            return objects.DayContext(
                day=day,
                tasks=tasks,
                events=preview_result.events,
                messages=preview_result.messages,
            )

    async def save_action(
        self,
        obj: HasActionsType,
        action: Action,
    ) -> HasActionsType:
        """Record an action on a task or event.

        Args:
            obj: The task or event to record the action on
            action: The action to record

        Returns:
            The updated object

        Raises:
            ValueError: If the object type is not supported
        """
        uow = self.uow_factory.create(self.user_id)
        async with uow:
            if isinstance(obj, Task):
                # Use domain method to record action
                obj.record_action(action)
                await uow.tasks.put(obj)

            elif isinstance(obj, Event):
                # Events don't have record_action yet, so use direct append
                obj.actions.append(action)
                await uow.events.put(obj)
            else:
                raise ValueError(f"Invalid object type: {type(obj)}")
            await uow.commit()
        return obj
