import asyncio

from loguru import logger

from planned import objects
from planned.repositories import task_repo
from planned.utils.dates import get_current_date

from .base import BaseService


class SheppardService(BaseService):
    running: bool = False

    async def run_loop(self) -> None:
        tasks: list[objects.Task] = await task_repo.search(
            get_current_date(),
        )

    async def run(self) -> None:
        logger.info("Starting Sheppard Service...")
        self.running = True
        while self.running:
            wait_time: int = 30
            try:
                logger.info("Syncing events...")
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
