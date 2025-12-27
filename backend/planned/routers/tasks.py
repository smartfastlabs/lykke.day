import datetime as dt
import uuid

from fastapi import APIRouter

from planned.objects import Action, BaseObject, Task, TaskStatus
from planned.repositories import task_repo
from planned.services import planning_svc
from planned.utils.dates import get_current_date

router = APIRouter()


@router.get("/today")
async def list_todays_tasks() -> list[Task]:
    return await task_repo.search(
        get_current_date(),
    )


@router.post("/{date}/{_id}/actions")
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: Action,
) -> Task:
    task: Task = await task_repo.get(date, str(_id))
    return await planning_svc.save_action(task, action)
