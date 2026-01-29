"""Admin API routes for domain event log and other admin features."""

import asyncio
import contextlib
import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.core.constants import DOMAIN_EVENT_LOG_KEY, DOMAIN_EVENT_STREAM_CHANNEL
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas.admin import (
    DomainEventListResponse,
    DomainEventSchema,
)

from .dependencies.admin import get_current_superuser, get_current_superuser_from_token

router = APIRouter()


def _get_redis_pool(request: Request) -> aioredis.ConnectionPool:
    """Get Redis connection pool from app state."""
    return request.app.state.redis_pool


@router.get("/events")
async def list_domain_events(
    request: Request,
    user: Annotated[UserEntity, Depends(get_current_superuser)],
    search: Annotated[
        str | None, Query(description="Text search in event data")
    ] = None,
    user_id: Annotated[str | None, Query(description="Filter by user ID")] = None,
    event_type: Annotated[
        str | None, Query(description="Filter by event type (partial match)")
    ] = None,
    start_time: Annotated[
        datetime | None, Query(description="Filter events after this time")
    ] = None,
    end_time: Annotated[
        datetime | None, Query(description="Filter events before this time")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DomainEventListResponse:
    """List domain events with optional filters.

    Returns paginated list of domain events from Redis, with optional filtering
    by search text, user_id, event_type, and time range.

    Only accessible by superusers.
    """
    redis_pool = _get_redis_pool(request)
    redis = aioredis.Redis(
        connection_pool=redis_pool,
        encoding="utf-8",
        decode_responses=True,
    )

    try:
        min_score = "-inf"
        max_score = "+inf"

        if start_time:
            min_score = str(int(start_time.timestamp() * 1000))
        if end_time:
            max_score = str(int(end_time.timestamp() * 1000))

        raw_events: list[str] = await redis.zrevrangebyscore(
            DOMAIN_EVENT_LOG_KEY,
            max_score,
            min_score,
        )

        events: list[DomainEventSchema] = []
        for raw_event in raw_events:
            try:
                event_data = json.loads(raw_event)
                event = DomainEventSchema(
                    id=event_data["id"],
                    event_type=event_data["event_type"],
                    event_data=event_data["event_data"],
                    stored_at=datetime.fromisoformat(event_data["stored_at"]),
                )

                if user_id:
                    event_user_id = event.event_data.get("user_id")
                    if not event_user_id or user_id not in str(event_user_id):
                        continue

                if event_type:
                    if event_type.lower() not in event.event_type.lower():
                        continue

                if search:
                    search_lower = search.lower()
                    event_str = json.dumps(event_data).lower()
                    if search_lower not in event_str:
                        continue

                events.append(event)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse domain event: {e}")
                continue

        total = len(events)
        paginated_events = events[offset : offset + limit]

        return DomainEventListResponse(
            items=paginated_events,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_previous=offset > 0,
        )

    finally:
        await redis.close()


@router.websocket("/events/stream")
async def domain_events_stream(
    websocket: WebSocket,
    user: Annotated[UserEntity, Depends(get_current_superuser_from_token)],
) -> None:
    """WebSocket endpoint for real-time domain event streaming.

    Streams new domain events as they are captured by the AuditEventHandler.
    Only accessible by superusers.
    """
    await websocket.accept()

    try:
        logger.info(f"Admin domain events WebSocket connected for superuser {user.id}")

        await websocket.send_json({"type": "connection_ack", "user_id": str(user.id)})

        redis_pool = websocket.app.state.redis_pool
        redis = aioredis.Redis(
            connection_pool=redis_pool,
            encoding="utf-8",
            decode_responses=True,
        )

        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe(DOMAIN_EVENT_STREAM_CHANNEL)

            receive_task = asyncio.create_task(_handle_client_messages_admin(websocket))
            stream_task = asyncio.create_task(_stream_events(websocket, pubsub))

            done, pending = await asyncio.wait(
                [receive_task, stream_task], return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        finally:
            await pubsub.unsubscribe(DOMAIN_EVENT_STREAM_CHANNEL)
            await pubsub.close()
            await redis.close()

    except WebSocketDisconnect:
        logger.info("Admin domain events WebSocket disconnected")

    except Exception as e:
        logger.error(f"Admin domain events WebSocket error: {e}")
        try:
            await websocket.send_json(
                {"type": "error", "message": "An unexpected error occurred"}
            )
            await websocket.close()
        except Exception:
            pass


async def _handle_client_messages_admin(websocket: WebSocket) -> None:
    """Handle incoming messages from admin WebSocket client.

    Currently just keeps the connection alive and handles ping/pong.
    """
    while True:
        try:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Error handling admin WebSocket message: {e}")
            break


async def _stream_events(
    websocket: WebSocket,
    pubsub: Any,
) -> None:
    """Stream domain events from Redis PubSub to WebSocket."""
    while True:
        try:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )

            if message and message["type"] == "message":
                event_data = message["data"]
                await websocket.send_json(
                    {"type": "domain_event", "data": json.loads(event_data)}
                )

        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Error streaming domain event: {e}")
            break
