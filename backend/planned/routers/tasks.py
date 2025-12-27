import datetime as dt
import uuid

from fastapi import APIRouter, Depends

from planned.objects import Action, Task
from planned.repositories import TaskRepository
from planned.services import PlanningService
from planned.utils.dates import get_current_date

from .dependencies.repositories import get_task_repo
from .dependencies.services import get_planning_service

router = APIRouter()


@router.get("/today")
async def list_todays_tasks(
    task_repo: TaskRepository = Depends(get_task_repo),
) -> list[Task]:
    return await task_repo.search(
        get_current_date(),
    )


@router.post("/{date}/{_id}/actions")
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: Action,
    task_repo: TaskRepository = Depends(get_task_repo),
    planning_service: PlanningService = Depends(get_planning_service),
) -> Task:
    task: Task = await task_repo.get(date, str(_id))
    return await planning_service.save_action(task, action)
