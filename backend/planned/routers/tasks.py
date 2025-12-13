import datetime as dt
import uuid

from fastapi import APIRouter, Request

from planned.objects import BaseObject, Task, TaskStatus
from planned.repositories import task_repo
from planned.utils.dates import get_current_date

router = APIRouter()


@router.get("/today")
async def list_todays_tasks() -> list[Task]:
    return await task_repo.search(
        get_current_date(),
    )


class UpdateTaskRequest(BaseObject):
    status: TaskStatus | None = None


@router.patch("/{date}/{id}")
async def update_task(
    request: UpdateTaskRequest,
    date: dt.date,
    id: uuid.UUID,
) -> Task:
    task: Task = await task_repo.get(date, str(id))

    if request.status:
        task.status = request.status

    return await task_repo.put(task)
