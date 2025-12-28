import asyncio
import contextlib
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

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
)
from planned.application.repositories.base import ChangeEvent
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
    WebSocket endpoint that streams all ChangeEvents from every repository class.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    # Queue to collect events from all repositories
    event_queue: asyncio.Queue[ChangeEvent[Any]] = asyncio.Queue()

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

    # Handler function to add events to the queue
    async def event_handler(
        _sender: object | None = None, *, event: ChangeEvent[Any]
    ) -> None:
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
