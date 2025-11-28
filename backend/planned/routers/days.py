from fastapi import APIRouter

from planned.objects import Day
from planned.services import planning_svc
from planned.utils.dates import get_current_date

router = APIRouter()


@router.put("/schedule/today")
async def schedule_today() -> Day:
    return await planning_svc.schedule_day(
        get_current_date(),
    )
