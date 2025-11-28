from fastapi import APIRouter

from planned.objects import Task
from planned.repositories import task_repo
from planned.utils.dates import get_current_date

router = APIRouter()




@router.get("/today")
async def list_todays_tasks() -> list[Task]:
    return await task_repo.search(
        get_current_date(),
    )
