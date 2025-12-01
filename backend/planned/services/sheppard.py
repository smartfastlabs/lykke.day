import asyncio
import datetime

from loguru import logger

from planned import objects
from planned.repositories import event_repo, message_repo, task_repo
from planned.utils.dates import get_current_date

from .base import BaseService
from .calendar import calendar_svc
from .day import day_svc


class SheppardService(BaseService):
    running: bool
    current_day: objects.Day

    def init(self, day: objects.Day) -> None:
        self.running = False
        self.current_day = day

    async def process_message(
        self,
        msg: objects.Message,
    ) -> list[objects.Message]:
        result: list[objects.Message] = []

        return result

    async def run_loop(
        self,
    ) -> None:
        day: objects.Day = await day_svc.load_day(get_current_date())

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
