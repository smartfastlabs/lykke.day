import datetime

from fastapi import APIRouter, Depends

from planned.domain.entities import DayContext, Routine
from planned.infrastructure.repositories import RoutineRepository
from planned.application.services import PlanningService
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from .dependencies.repositories import get_routine_repo
from .dependencies.services import get_planning_service

router = APIRouter()


@router.get("/routines")
async def list_routines(
    routine_repo: RoutineRepository = Depends(get_routine_repo),
) -> list[Routine]:
    return await routine_repo.all()


@router.put("/schedule/today")
async def schedule_today(
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.schedule(get_current_date())


@router.get("/preview/today")
async def preview_today(
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.preview(get_current_date())


@router.get("/tomorrow/preview")
async def preview_tomorrow(
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.preview(get_tomorrows_date())


@router.put("/tomorrow/schedule")
async def schedule_tomorrow(
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.schedule(get_tomorrows_date())


@router.get("/date/{date}/preview")
async def preview_date(
    date: datetime.date,
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.preview(date)


@router.put("/date/{date}/schedule")
async def schedule_date(
    date: datetime.date,
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.schedule(date)
