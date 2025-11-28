from fastapi import APIRouter

from planned.objects import Routine
from planned.repositories import routine_repo

router = APIRouter()


@router.get("/")
async def list_routines() -> list[Routine]:
    return await routine_repo.search()