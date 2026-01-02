"""SheppardService for managing day scheduling and notifications."""

import asyncio
import datetime
from datetime import UTC
from typing import Any, Literal

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from loguru import logger
from planned.application.commands.save_day import SaveDayCommand, SaveDayHandler
from planned.application.gateways.web_push_protocol import WebPushGatewayProtocol
from planned.application.queries.get_upcoming_items import (
    GetUpcomingCalendarEntriesHandler,
    GetUpcomingCalendarEntriesQuery,
    GetUpcomingTasksHandler,
    GetUpcomingTasksQuery,
)
from planned.application.services.base import BaseService
from planned.application.services.calendar import CalendarService
from planned.application.services.day import DayService
from planned.application.services.day.factory import DayServiceFactory
from planned.application.services.planning import PlanningService
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import entities, value_objects
from planned.domain.services.notification import NotificationPayloadBuilder
from planned.infrastructure.utils import templates, youtube
from planned.infrastructure.utils.dates import get_current_date, get_current_time


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def notifiy_user(message: str, urgency: Literal["low", "medium", "high"]) -> None:
    pass


def filter_tasks(tasks: list[entities.Task]) -> list[entities.Task]:
    tasks = [t for t in tasks if t.status == "READY"]
    return tasks


SheppardMode = Literal[
    "active",
    "sleeping",
    "stopping",
    "starting",
]


# TODO: Consider renaming SheppardService to DaySchedulerService or NotificationService
# for better clarity. "Sheppard" is unclear and doesn't convey the service's purpose.
class SheppardService(BaseService):
    """Service for managing day scheduling and notifications."""

    agent: Runnable
    day_svc: DayService
    mode: SheppardMode
    last_run: datetime.datetime | None = None
    push_subscriptions: list[entities.PushSubscription] = []
    uow_factory: UnitOfWorkFactory
    calendar_service: CalendarService
    planning_service: PlanningService
    web_push_gateway: WebPushGatewayProtocol
    _get_upcoming_tasks_handler: GetUpcomingTasksHandler
    _get_upcoming_calendar_entries_handler: GetUpcomingCalendarEntriesHandler
    _save_day_handler: SaveDayHandler

    def __init__(
        self,
        user: entities.User,
        day_svc: DayService,
        uow_factory: UnitOfWorkFactory,
        calendar_service: CalendarService,
        planning_service: PlanningService,
        web_push_gateway: WebPushGatewayProtocol,
        push_subscriptions: list[entities.PushSubscription] | None = None,
        mode: SheppardMode = "starting",
    ) -> None:
        """Initialize SheppardService.

        Args:
            user: The user for this service
            day_svc: DayService instance for managing day context
            uow_factory: Factory for creating UnitOfWork instances
            calendar_service: CalendarService for syncing calendars
            planning_service: PlanningService for scheduling
            web_push_gateway: Gateway for web push notifications
            push_subscriptions: List of push subscriptions for the user
            mode: Initial mode of the service
        """
        super().__init__(user)
        self.mode = mode
        self.uow_factory = uow_factory
        self.calendar_service = calendar_service
        self.planning_service = planning_service
        self.web_push_gateway = web_push_gateway
        self.push_subscriptions = push_subscriptions or []
        self.last_run = None
        self.day_svc = day_svc
        self._get_upcoming_tasks_handler = GetUpcomingTasksHandler(uow_factory)
        self._get_upcoming_calendar_entries_handler = GetUpcomingCalendarEntriesHandler(
            uow_factory
        )
        self._save_day_handler = SaveDayHandler(uow_factory)
        self.agent = create_agent(
            model="claude-sonnet-4-5",
            tools=[get_weather],
            system_prompt="You are a helpful assistant",
        )

    async def run_loop(
        self,
    ) -> None:
        """Main loop that runs periodically to handle day operations."""
        await self._check_and_handle_day_transition()
        await self._handle_alarm()

        tasks_to_update, tasks_to_notify = await self._process_upcoming_tasks()
        calendar_entries_to_notify = await self._process_upcoming_calendar_entries()

        await self._save_updates_and_send_notifications(
            tasks_to_update=tasks_to_update,
            tasks_to_notify=tasks_to_notify,
            calendar_entries_to_notify=calendar_entries_to_notify,
        )

        self.last_run = datetime.datetime.now(UTC)

    async def _check_and_handle_day_transition(self) -> None:
        """Check if the day has changed and handle the transition."""
        current_date = get_current_date()
        if current_date != self.day_svc.date:
            await self.end_day()
            await self.start_day()

    async def _handle_alarm(self) -> None:
        """Check and trigger alarm if it's time."""
        current_time: datetime.time = get_current_time()
        day_ctx = await self.day_svc.load_context()
        if alarm := day_ctx.day.alarm:  # noqa
            if alarm.triggered_at is None and alarm.time < current_time:
                alarm.triggered_at = current_time
                logger.info(f"Triggering alarm: {alarm.name} at {alarm.time}")

                youtube.play_audio("https://www.youtube.com/watch?v=Gcv7re2dEVg")
                cmd = SaveDayCommand(user_id=self.user.id, day=day_ctx.day)
                await self._save_day_handler.handle(cmd)

    async def _process_upcoming_tasks(
        self,
    ) -> tuple[list[entities.Task], list[entities.Task]]:
        """Process upcoming tasks and determine which need updates and notifications.

        Returns:
            Tuple of (tasks_to_update, tasks_to_notify)
        """
        tasks_to_notify: list[entities.Task] = []
        tasks_to_update: list[entities.Task] = []

        query = GetUpcomingTasksQuery(
            user=self.user, date=self.day_svc.date
        )
        upcoming_tasks = await self._get_upcoming_tasks_handler.handle(query)

        for task in upcoming_tasks:
            logger.info(f"UPCOMING TASK {task.name}")

            # Update task status if needed
            if task.status != value_objects.TaskStatus.PENDING:
                task.mark_pending()
                tasks_to_update.append(task)

            # Check if this task needs a notification
            if not any(
                action.type == value_objects.ActionType.NOTIFY for action in task.actions
            ):
                tasks_to_notify.append(task)
                task.record_action(
                    entities.Action(
                        type=value_objects.ActionType.NOTIFY,
                    )
                )

        return tasks_to_update, tasks_to_notify

    async def _process_upcoming_calendar_entries(
        self,
    ) -> list[entities.CalendarEntry]:
        """Process upcoming calendar entries and determine which need notifications.

        Returns:
            List of calendar entries that need notifications
        """
        calendar_entries_to_notify: list[entities.CalendarEntry] = []

        query = GetUpcomingCalendarEntriesQuery(
            user=self.user, date=self.day_svc.date
        )
        upcoming_calendar_entries = await self._get_upcoming_calendar_entries_handler.handle(
            query
        )

        for calendar_entry in upcoming_calendar_entries:
            logger.info(f"UPCOMING CALENDAR ENTRY {calendar_entry.name}")

            # Check if this calendar entry needs a notification
            if not any(
                action.type == value_objects.ActionType.NOTIFY
                for action in calendar_entry.actions
            ):
                calendar_entries_to_notify.append(calendar_entry)
                calendar_entry.actions.append(
                    entities.Action(
                        type=value_objects.ActionType.NOTIFY,
                    )
                )

        return calendar_entries_to_notify

    async def _save_updates_and_send_notifications(
        self,
        tasks_to_update: list[entities.Task],
        tasks_to_notify: list[entities.Task],
        calendar_entries_to_notify: list[entities.CalendarEntry],
    ) -> None:
        """Save updates to database and send notifications.

        Args:
            tasks_to_update: Tasks that need to be saved to database
            tasks_to_notify: Tasks that need notifications sent
            calendar_entries_to_notify: Calendar entries that need notifications sent
        """
        # Wrap database operations in a transaction
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            # Save all updated tasks
            for task in tasks_to_update:
                await uow.tasks.put(task)

            # Save all calendar entries that were notified (they all got NOTIFY actions added)
            for calendar_entry in calendar_entries_to_notify:
                await uow.calendar_entries.put(calendar_entry)

            # Commit transaction
            await uow.commit()

        # Send notifications after transaction commits
        if tasks_to_notify:
            await self._notify_for_tasks(tasks_to_notify)

        if calendar_entries_to_notify:
            await self._notify_for_calendar_entries(calendar_entries_to_notify)


    async def _notify_for_tasks(
        self,
        tasks: list[entities.Task],
    ) -> None:
        """Send notifications for the given tasks to all push subscriptions."""
        if not tasks:
            return

        payload = NotificationPayloadBuilder.build_for_tasks(tasks)

        for subscription in self.push_subscriptions:
            logger.info(
                f"Sending notification for {len(tasks)} task(s) to {subscription.endpoint}"
            )
            try:
                await self.web_push_gateway.send_notification(
                    subscription=subscription,
                    content=payload,
                )
            except Exception as e:
                logger.exception(
                    f"Failed to send notification to {subscription.endpoint}: {e}"
                )


    async def _notify_for_calendar_entries(
        self,
        calendar_entries: list[entities.CalendarEntry],
    ) -> None:
        """Send notifications for the given calendar entries to all push subscriptions."""
        if not calendar_entries:
            return

        payload = NotificationPayloadBuilder.build_for_calendar_entries(
            calendar_entries
        )

        for subscription in self.push_subscriptions:
            logger.info(
                f"Sending notification for {len(calendar_entries)} calendar entry(ies) to {subscription.endpoint}"
            )
            try:
                await self.web_push_gateway.send_notification(
                    subscription=subscription,
                    content=payload,
                )
            except Exception as e:
                logger.exception(
                    f"Failed to send notification to {subscription.endpoint}: {e}"
                )

    async def _render_prompt(self, template_name: str, **kwargs: Any) -> str:
        day_ctx = await self.day_svc.load_context()
        return templates.render(
            template_name,
            current_time=get_current_time(),
            tasks=day_ctx.tasks,
            calendar_entries=day_ctx.calendar_entries,
            **kwargs,
        )

    async def morning_summary_prompt(self) -> str:
        return await self._render_prompt(
            "morning-summary.md",
        )

    async def evening_summary_prompt(self) -> str:
        return await self._render_prompt(
            "evening-summary.md",
        )

    async def end_day(self) -> None:
        # Cleanup tasks, send summary, etc.
        # Make sure tomorrow's day is scheduled
        pass

    async def start_day(self, _: str = "default") -> None:
        """Start a new day.

        Confirms yesterday is ended, schedules today if not already scheduled,
        and updates the day service to the new date.
        """
        date = get_current_date()

        # Create a DayService instance using the factory
        factory = DayServiceFactory(
            user=self.user,
            uow_factory=self.uow_factory,
        )
        self.day_svc = await factory.create(date, user_id=self.user.id)

        # Check if day needs to be scheduled
        day_ctx = await self.day_svc.load_context()
        if day_ctx.day.status != value_objects.DayStatus.SCHEDULED:
            await self.planning_service.schedule(self.day_svc.date)

    async def run(self) -> None:
        logger.info("Starting Sheppard Service...")
        self.mode = "active"
        while self.is_running:
            wait_time: int = 30
            try:
                logger.info("Syncing events...")
                await self.calendar_service.sync_all()
            except Exception as e:
                logger.exception(f"Error during sync: {e}")
                wait_time = 10
            else:
                try:
                    await self.run_loop()
                except Exception as e:
                    logger.exception(f"Error during Sheppard Loop: {e}")
                    wait_time = 10

            # Sleep in small steps so we can stop quickly
            while self.is_running and wait_time >= 0:
                wait_time -= 1
                await asyncio.sleep(1)

    def stop(self) -> None:
        self.mode = "stopping"

    @property
    def is_running(self) -> bool:
        return self.mode not in ("stopping", "starting")

