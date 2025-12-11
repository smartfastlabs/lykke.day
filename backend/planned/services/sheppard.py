import asyncio
import datetime
from textwrap import dedent
from typing import Any, Literal

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from loguru import logger

from planned import objects
from planned.utils import templates, youtube
from planned.utils.dates import get_current_date, get_current_datetime, get_current_time

from .base import BaseService
from .calendar import calendar_svc
from .day import DayService
from .planning import planning_svc


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

    def __init__(
        self,
        day_svc: DayService,
        mode: SheppardMode = "starting",
    ) -> None:
        self.mode = mode
        self.last_run = None
        self.day_svc = day_svc
        self.agent = create_agent(
            model="claude-sonnet-4-5",
            tools=[get_weather],
            system_prompt="You are a helpful assistant",
        )

    @classmethod
    async def new(cls) -> "SheppardService":
        day_svc = await DayService.for_date(get_current_date())
        return cls(day_svc=day_svc)

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
        self.day_svc = await DayService.for_date(get_current_date())

        if self.day_svc.ctx.day.status != objects.DayStatus.SCHEDULED:
            await planning_svc.schedule(self.day_svc.date)

    async def run(self) -> None:
        logger.info("Starting Sheppard Service...")
        self.mode = "active"
        while self.is_running:
            wait_time: int = 30
            try:
                logger.info("Syncing events...")
                await calendar_svc.sync_all()
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
