import asyncio
import datetime
from textwrap import dedent
from typing import Any, Literal

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from loguru import logger

from planned import objects
from planned.gateways import web_push
from planned.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    PushSubscriptionRepository,
    TaskRepository,
)
from planned.utils import templates, youtube
from planned.utils.dates import get_current_date, get_current_datetime, get_current_time

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
    push_subscription_repo: PushSubscriptionRepository
    task_repo: TaskRepository
    calendar_service: CalendarService
    planning_service: PlanningService
    day_repo: DayRepository
    day_template_repo: DayTemplateRepository
    event_repo: EventRepository
    message_repo: MessageRepository

    def __init__(
        self,
        day_svc: DayService,
        push_subscription_repo: PushSubscriptionRepository,
        task_repo: TaskRepository,
        calendar_service: CalendarService,
        planning_service: PlanningService,
        day_repo: DayRepository,
        day_template_repo: DayTemplateRepository,
        event_repo: EventRepository,
        message_repo: MessageRepository,
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

        for task in await self.day_svc.get_upcomming_tasks():
            if task.status != objects.TaskStatus.PENDING:
                task.status = objects.TaskStatus.PENDING

                if not any(
                    action.type == objects.ActionType.NOTIFY for action in task.actions
                ):
                    for subscription in self.push_subscriptions:
                        logger.info(f"Sending notification to {subscription.endpoint}")
                        await web_push.send_notification(
                            subscription=subscription,
                            content=objects.NotificationPayload(
                                title="Notifications Enabled!",
                                body="TASK NOTIFICATION",
                                actions=[
                                    objects.NotificationAction(
                                        action="view",
                                        title="View Task",
                                        icon="🔍",
                                    ),
                                ],
                            ),
                        )

                    task.actions.append(
                        objects.Action(
                            type=objects.ActionType.NOTIFY,
                        ),
                    )
                await self.task_repo.put(task)

            logger.info(f"UPCOMING TASK {task.name}")

        for event in await self.day_svc.get_upcomming_events():
            logger.info(f"UPCOMING EVENT{event.name}")

        prompt = self.checkin_prompt()

        self.last_run = datetime.datetime.now()

    def _render_prompt(self, template_name: str, **kwargs: Any) -> str:
        return templates.render(
            template_name,
            current_time=get_current_time(),
            tasks=self.day_svc.ctx.tasks,
            events=self.day_svc.ctx.events,
            **kwargs,
        )

    def checkin_prompt(self) -> str:
        return self._render_prompt(
            "check-in.md",
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
