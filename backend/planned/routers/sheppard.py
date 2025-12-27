from fastapi import APIRouter

from planned.utils import youtube

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
