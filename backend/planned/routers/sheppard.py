from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter, Depends

from planned.objects import DayContext, Task
from planned.repositories import event_repo, task_repo
from planned.services import DayService
from planned.utils.dates import get_current_date

router = APIRouter()


@router.put("/prompts/{prompt_name}")
async def schedule_today(
    prompt_name: str,
) -> DayContext:
    return await (await DayService.for_date(get_current_date()))


@router.get("/today")
async def get_today() -> DayContext:
    return (await DayService.for_date(get_current_date())).ctx


@router.put("/day/start")
async def start_day() -> DayContext:
    return (await DayService.for_date(get_current_date())).ctx
