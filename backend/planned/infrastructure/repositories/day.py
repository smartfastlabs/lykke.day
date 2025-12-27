import os

from planned.core.config import settings
from planned.domain.entities import Day

from .base import BaseCrudRepository


class DayRepository(BaseCrudRepository[Day]):
    Object = Day
    _prefix = "days"

    def _get_file_path(self, key: str) -> str:
        return os.path.abspath(f"{settings.DATA_PATH}/dates/{key}/day.json")

    async def all(self) -> list[Day]:
        raise NotImplementedError
