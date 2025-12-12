from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter, Depends

from planned.objects import DayContext, Task
from planned.repositories import event_repo, task_repo
from planned.services import DayService
from planned.utils import youtube
from planned.utils.dates import get_current_date

router = APIRouter()


@router.put("/prompts/{prompt_name}")
async def prompts(
    prompt_name: str,
) -> str:
    return f"This is a placeholder response for prompt: {prompt_name}"


@router.put("/stop-alarm")
async def stop_alarm() -> None:
    youtube.kill_current_player()


@router.get("/start-alarm")
async def start_alarm() -> None:
    youtube.play_audio("https://www.youtube.com/watch?v=Gcv7re2dEVg")
