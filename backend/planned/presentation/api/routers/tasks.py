import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.repositories import TaskRepositoryProtocol
from planned.application.services import PlanningService
from planned.domain.entities import Action, Task
from planned.domain.value_objects.query import DateQuery
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.repositories import get_task_repo
from .dependencies.services import get_planning_service

router = APIRouter()


@router.get("/today")
async def list_todays_tasks(
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> list[Task]:
    return await task_repo.search_query(DateQuery(date=get_current_date()))


@router.post("/{date}/{_id}/actions")
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: Action,
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
) -> Task:
    task: Task = await task_repo.get(_id)
    return await planning_service.save_action(task, action)
