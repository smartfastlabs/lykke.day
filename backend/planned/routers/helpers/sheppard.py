import datetime

from fastapi import Depends

from planned.services import DayService, SheppardService
from planned.utils.dates import get_current_date

from .days import load_todays_day_svc


async def load_sheppard_svc(
    date: datetime.date,
    day_svc: DayService = Depends(load_todays_day_svc),
) -> SheppardService:
    return SheppardService(day_svc=day_svc)
