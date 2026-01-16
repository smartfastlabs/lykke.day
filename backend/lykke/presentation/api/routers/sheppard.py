from fastapi import APIRouter
from lykke.core.utils import youtube

router = APIRouter()


@router.put("/stop-alarm")
async def stop_alarm() -> None:
    youtube.kill_current_player()
