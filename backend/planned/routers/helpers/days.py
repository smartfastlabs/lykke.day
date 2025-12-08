import datetime

from planned.services import DayService
from planned.utils.dates import get_current_date


async def load_day_svc(date: datetime.date) -> DayService:
    return await DayService.for_date(date)


async def load_todays_day_svc() -> DayService:
    return await DayService.for_date(get_current_date())
