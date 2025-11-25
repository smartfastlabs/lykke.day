from fastapi import APIRouter

from planned.objects import Routine, RoutineInstance
from planned.repositories import routine_instance_repo, routine_repo
from planned.utils.dates import get_current_date

router = APIRouter()


@router.get("/")
async def list_routines() -> list[Routine]:
    return await routine_repo.search()


@router.get("/instances/today")
async def list_todays_routine_instances() -> list[RoutineInstance]:
    return await routine_instance_repo.search(
        get_current_date(),
    )
