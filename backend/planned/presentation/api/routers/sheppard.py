import asyncio
import contextlib
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from planned.application.services import SheppardManager
from planned.core.exceptions import exceptions
from planned.domain.value_objects.repository_event import RepositoryEvent
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    UserRepository,
)
from planned.infrastructure.repositories.base.repository import BaseRepository
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
    WebSocket endpoint that streams RepositoryEvents from the logged-in user's repositories.
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
    except exceptions.NotFoundError:
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

    # Queue to collect events from all repositories
    event_queue: asyncio.Queue[RepositoryEvent[Any]] = asyncio.Queue()

    # Get all repository classes
    repository_classes: list[type[BaseRepository[Any, Any]]] = [
        AuthTokenRepository,
        CalendarRepository,
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        PushSubscriptionRepository,
        RoutineRepository,
        TaskDefinitionRepository,
        TaskRepository,
    ]

    # Handler function to add events to the queue, filtered by user
    async def event_handler(
        _sender: object | None = None, *, event: RepositoryEvent[Any]
    ) -> None:
        # Filter events to only those for the logged-in user
        # Check if the event value has a user_id attribute
        event_value = event.value
        if hasattr(event_value, "user_id"):
            event_user_id = (
                UUID(event_value.user_id)
                if isinstance(event_value.user_id, str)
                else event_value.user_id
            )
            if event_user_id == user_id:
                await event_queue.put(event)

    # Subscribe to all repository signals
    for repo_class in repository_classes:
        repo_class.signal_source.connect(event_handler)
        logger.debug(f"Subscribed to {repo_class.__name__} signals")

    try:
        # Task to send events from queue to websocket
        async def send_events() -> None:
            while True:
                try:
                    event = await event_queue.get()
                    # Serialize the event to JSON
                    event_json = event.model_dump_json()
                    await websocket.send_text(event_json)
                except (WebSocketDisconnect, RuntimeError) as e:
                    logger.exception(f"Error sending event: {e}")
                    break

        # Start the send task
        send_task = asyncio.create_task(send_events())

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

        # Cancel the send task when connection closes
        send_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await send_task

    finally:
        # Unsubscribe from all repository signals
        for repo_class in repository_classes:
            repo_class.signal_source.disconnect(event_handler)
            logger.debug(f"Unsubscribed from {repo_class.__name__} signals")
