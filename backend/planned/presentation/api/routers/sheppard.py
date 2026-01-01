from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from planned.application.services import SheppardManager
from planned.core.exceptions import NotFoundError
from planned.infrastructure.repositories import UserRepository
from planned.infrastructure.utils import youtube

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


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for the logged-in user.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    # Get user from session
    session = getattr(websocket, "session", {})
    user_id_str = session.get("user_id")

    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        await websocket.close(code=1008, reason="Invalid session data")
        return

    # Get user to verify it exists
    user_repo = UserRepository()
    try:
        await user_repo.get(user_id)
    except NotFoundError:
        await websocket.close(code=1008, reason="User not found")
        return

    # Get SheppardManager from app state
    manager: SheppardManager | None = getattr(
        websocket.app.state, "sheppard_manager", None
    )
    if manager is None:
        logger.error("SheppardManager is not available")
        await websocket.close(code=1011, reason="Service unavailable")
        return

    # Ensure sheppard service exists for the user (starting it if necessary)
    try:
        await manager.ensure_service_for_user(user_id)
    except RuntimeError as e:
        logger.error(f"Failed to ensure SheppardService for user {user_id}: {e}")
        await websocket.close(code=1011, reason="Service unavailable")
        return

    logger.info(f"WebSocket connected for user {user_id}")

    try:
        # Keep connection alive and handle disconnections
        while True:
            try:
                # Wait for client to disconnect or send a message
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
                logger.debug(f"Received message from client: {data}")
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except (RuntimeError, ValueError) as e:
                logger.exception(f"WebSocket error: {e}")
                break
    finally:
        logger.info(f"WebSocket connection closed for user {user_id}")
