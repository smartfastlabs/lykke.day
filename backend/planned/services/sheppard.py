import asyncio
from textwrap import dedent
from typing import Literal

from langchain.agents import create_agent
from langchain_core.runnables import Runnable
from loguru import logger

from planned import objects
from planned.repositories import event_repo, message_repo, task_repo
from planned.utils import templates
from planned.utils.dates import get_current_date, get_current_time

from .base import BaseService
from .calendar import calendar_svc
from .day import DayService


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def notifiy_user(message: str, urgency: Literal["low", "medium", "high"]) -> None:
    pass


def filter_tasks(tasks: list[objects.Task]) -> list[objects.Task]:
    tasks = [t for t in tasks if t.status == "READY"]
    return tasks


class SheppardService(BaseService):
    running: bool
    agent: Runnable

    def __init__(self) -> None:
        self.agent = create_agent(
            model="claude-sonnet-4-5",
            tools=[get_weather],
            system_prompt="You are a helpful assistant",
        )

        self.running = False

    async def process_message(
        self,
        msg: objects.Message,
    ) -> list[objects.Message]:
        result: list[objects.Message] = []

        return result

    async def run_loop(
        self,
    ) -> None:
        day: objects.DayContext = await DayService(get_current_date()).load_context()
        prompt = templates.render(
            "check-in.md",
            current_time=get_current_time(),
            tasks=day.tasks,
            events=day.events,
        )

    async def run(self) -> None:
        logger.info("Starting Sheppard Service...")
        self.running = True
        while self.running:
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
            while self.running and wait_time >= 0:
                wait_time -= 1
                await asyncio.sleep(1)

    def stop(self) -> None:
        self.running = False


sheppard_svc = SheppardService()
