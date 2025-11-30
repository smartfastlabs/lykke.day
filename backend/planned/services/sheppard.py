import asyncio
import datetime

from loguru import logger

from planned import objects
from planned.repositories import event_repo, message_repo, task_repo
from planned.utils.dates import get_current_date

from .base import BaseService
from .calendar import calendar_svc
from .routine import routine_svc


class SheppardService(BaseService):
    running: bool
    current_day: objects.Day

    def init(self, day: objects.Day) -> None:
        self.running = False
        self.current_day = day

    async def schedule_day(
        self,
        date: datetime.date,
    ) -> objects.Day:
        await routine_svc.schedule(date)

        return await self.load_day(date)

    async def load_day(
        self,
        date: datetime.date,
    ) -> objects.Day:
        tasks: list[objects.Task]
        events: list[objects.Event]
        messages: list[objects.Message]

        tasks, events, messages = await asyncio.gather(
            task_repo.search(date),
            event_repo.search(date),
            message_repo.search(date),
        )

        return objects.Day(
            date=date,
            tasks=tasks,
            events=events,
            messages=messages,
        )

    async def process_message(
        self,
        msg: objects.Message,
    ) -> list[objects.Message]:
        result: list[objects.Message] = []

        return result

    async def run_loop(
        self,
    ) -> None:
        return None

    async def run(self) -> None:
        logger.info("Starting Sheppard Service...")
        self.running = True
        while self.running:
            wait_time: int = 30
            try:
                logger.info("Syncing events...")
                await calendar_svc.sync_all()
            except Exception as e:
                logger.info(f"Error during sync: {e}")
                wait_time = 10
            else:
                try:
                    await self.run_loop()
                except Exception as e:
                    logger.info(f"Error during sync: {e}")
                    wait_time = 10

            # Sleep in small steps so we can stop quickly
            while self.running and wait_time >= 0:
                wait_time -= 1
                await asyncio.sleep(1)

    def stop(self) -> None:
        self.running = False


sheppard_svc = SheppardService()
