import asyncio
import datetime
from datetime import UTC
from typing import Any, Literal

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from loguru import logger
from planned.application.gateways.web_push_protocol import WebPushGatewayProtocol
from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.domain import entities as objects
from planned.infrastructure.utils import templates, youtube
from planned.infrastructure.utils.dates import get_current_date, get_current_time

from .base import BaseService
from .calendar import CalendarService
from .day import DayService
from .planning import PlanningService


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def notifiy_user(message: str, urgency: Literal["low", "medium", "high"]) -> None:
    pass


def filter_tasks(tasks: list[objects.Task]) -> list[objects.Task]:
    tasks = [t for t in tasks if t.status == "READY"]
    return tasks


SheppardMode = Literal[
    "active",
    "sleeping",
    "stopping",
    "starting",
]


class SheppardService(BaseService):
    agent: Runnable
    day_svc: DayService
    mode: SheppardMode
    last_run: datetime.datetime | None = None
    push_subscriptions: list[objects.PushSubscription] = []
    push_subscription_repo: PushSubscriptionRepositoryProtocol
    task_repo: TaskRepositoryProtocol
    calendar_service: CalendarService
    planning_service: PlanningService
    day_repo: DayRepositoryProtocol
    day_template_repo: DayTemplateRepositoryProtocol
    event_repo: EventRepositoryProtocol
    message_repo: MessageRepositoryProtocol
    web_push_gateway: WebPushGatewayProtocol

    def __init__(
        self,
        day_svc: DayService,
        push_subscription_repo: PushSubscriptionRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        calendar_service: CalendarService,
        planning_service: PlanningService,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        web_push_gateway: WebPushGatewayProtocol,
        push_subscriptions: list[objects.PushSubscription] | None = None,
        mode: SheppardMode = "starting",
    ) -> None:
        self.mode = mode
        self.push_subscription_repo = push_subscription_repo
        self.task_repo = task_repo
        self.calendar_service = calendar_service
        self.planning_service = planning_service
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.event_repo = event_repo
        self.message_repo = message_repo
        self.web_push_gateway = web_push_gateway
        self.push_subscriptions = push_subscriptions or []
        self.last_run = None
        self.day_svc = day_svc
        self.agent = create_agent(
            model="claude-sonnet-4-5",
            tools=[get_weather],
            system_prompt="You are a helpful assistant",
        )

    async def run_loop(
        self,
    ) -> None:
        if get_current_date() != self.day_svc.date:
            await self.end_day()
            await self.start_day()

        current_time: datetime.time = get_current_time()
        if alarm := self.day_svc.ctx.day.alarm:  # noqa
            if alarm.triggered_at is None and alarm.time < current_time:
                alarm.triggered_at = current_time
                logger.info(f"Triggering alarm: {alarm.name} at {alarm.time}")

                youtube.play_audio("https://www.youtube.com/watch?v=Gcv7re2dEVg")
                await self.day_svc.save()

        # Collect tasks that need notifications
        tasks_to_notify: list[objects.Task] = []
        tasks_to_update: list[objects.Task] = []

        for task in await self.day_svc.get_upcomming_tasks():
            if task.status != objects.TaskStatus.PENDING:
                task.status = objects.TaskStatus.PENDING
                tasks_to_update.append(task)

                # Check if this task needs a notification
                if not any(
                    action.type == objects.ActionType.NOTIFY for action in task.actions
                ):
                    tasks_to_notify.append(task)
                    task.actions.append(
                        objects.Action(
                            type=objects.ActionType.NOTIFY,
                        ),
                    )

            logger.info(f"UPCOMING TASK {task.name}")

        # Collect events that need notifications
        events_to_notify: list[objects.Event] = []

        for event in await self.day_svc.get_upcomming_events():
            logger.info(f"UPCOMING EVENT {event.name}")

            # Check if this event needs a notification
            if not any(
                action.type == objects.ActionType.NOTIFY for action in event.actions
            ):
                events_to_notify.append(event)
                event.actions.append(
                    objects.Action(
                        type=objects.ActionType.NOTIFY,
                    ),
                )

        # Wrap database operations in a transaction
        async with self.transaction():
            # Save all updated tasks
            for task in tasks_to_update:
                await self.task_repo.put(task)

            # Save all events that were notified (they all got NOTIFY actions added)
            for event in events_to_notify:
                await self.event_repo.put(event)

        # Send notifications after transaction commits
        if tasks_to_notify:
            await self._notify_for_tasks(tasks_to_notify)

        if events_to_notify:
            await self._notify_for_events(events_to_notify)

        self.last_run = datetime.datetime.now(UTC)

    def _build_notification_payload(
        self,
        tasks: list[objects.Task],
    ) -> objects.NotificationPayload:
        """Build a notification payload for one or more tasks."""
        if len(tasks) == 1:
            task = tasks[0]
            title = task.name
            body = f"Task ready: {task.name}"
        else:
            title = f"{len(tasks)} tasks ready"
            body = f"You have {len(tasks)} tasks ready"

        # Include task information in the data field
        task_data = [
            {
                "uuid": task.uuid,
                "name": task.name,
                "status": task.status.value,
                "category": task.category.value,
            }
            for task in tasks
        ]

        return objects.NotificationPayload(
            title=title,
            body=body,
            actions=[
                objects.NotificationAction(
                    action="view",
                    title="View Tasks",
                    icon="🔍",
                ),
            ],
            data={
                "type": "tasks",
                "task_uuids": [task.uuid for task in tasks],
                "tasks": task_data,
            },
        )

    async def _notify_for_tasks(
        self,
        tasks: list[objects.Task],
    ) -> None:
        """Send notifications for the given tasks to all push subscriptions."""
        if not tasks:
            return

        payload = self._build_notification_payload(tasks)

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

    def _build_event_notification_payload(
        self,
        events: list[objects.Event],
    ) -> objects.NotificationPayload:
        """Build a notification payload for one or more events."""
        if len(events) == 1:
            event = events[0]
            title = event.name
            body = f"Event starting soon: {event.name}"
        else:
            title = f"{len(events)} events starting soon"
            body = f"You have {len(events)} events starting soon"

        # Include event information in the data field
        event_data = [
            {
                "uuid": event.uuid,
                "name": event.name,
                "starts_at": event.starts_at.isoformat(),
                "ends_at": event.ends_at.isoformat() if event.ends_at else None,
                "calendar_uuid": event.calendar_uuid,
                "platform_id": event.platform_id,
                "status": event.status,
            }
            for event in events
        ]

        return objects.NotificationPayload(
            title=title,
            body=body,
            actions=[
                objects.NotificationAction(
                    action="view",
                    title="View Events",
                    icon="📅",
                ),
            ],
            data={
                "type": "events",
                "event_uuids": [event.uuid for event in events],
                "events": event_data,
            },
        )

    async def _notify_for_events(
        self,
        events: list[objects.Event],
    ) -> None:
        """Send notifications for the given events to all push subscriptions."""
        if not events:
            return

        payload = self._build_event_notification_payload(events)

        for subscription in self.push_subscriptions:
            logger.info(
                f"Sending notification for {len(events)} event(s) to {subscription.endpoint}"
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

    def _render_prompt(self, template_name: str, **kwargs: Any) -> str:
        return templates.render(
            template_name,
            current_time=get_current_time(),
            tasks=self.day_svc.ctx.tasks,
            events=self.day_svc.ctx.events,
            **kwargs,
        )

    def morning_summary_prompt(self) -> str:
        return self._render_prompt(
            "morning-summary.md",
        )

    def evening_summary_prompt(self) -> str:
        return self._render_prompt(
            "evening-summary.md",
        )

    async def end_day(self) -> None:
        # Cleanup tasks, send summary, etc.
        # Make sure tomorrow's day is scheduled
        pass

    async def start_day(self, template: str = "default") -> None:
        # Confirm yesterday is ended
        # If it is not already scheduled, schedule
        # Update the day service to the new date
        # send morning summary
        self.day_svc = await DayService.for_date(
            get_current_date(),
            user_uuid=self.planning_service.user_uuid,
            day_repo=self.day_repo,
            day_template_repo=self.day_template_repo,
            event_repo=self.event_repo,
            message_repo=self.message_repo,
            task_repo=self.task_repo,
        )

        if self.day_svc.ctx.day.status != objects.DayStatus.SCHEDULED:
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
