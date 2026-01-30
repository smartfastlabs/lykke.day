"""Admin API routes for the structured-log backlog and stream."""

import asyncio
import contextlib
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.admin import (
    ListStructuredLogEventsHandler,
    ListStructuredLogEventsQuery,
)
from lykke.application.gateways.structured_log_backlog_protocol import (
    StructuredLogBacklogStreamGatewayProtocol,
    StructuredLogBacklogStreamSubscription,
)
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas.admin import (
    DomainEventListResponse,
    DomainEventSchema,
)

from .dependencies.admin import get_current_superuser, get_current_superuser_from_token
from .dependencies.services import (
    get_list_structured_log_events_handler,
    get_structured_log_backlog_stream_gateway,
)

router = APIRouter()


@router.get("/events")
async def list_structured_log_events(
    request: Request,
    user: Annotated[UserEntity, Depends(get_current_superuser)],
    handler: Annotated[
        ListStructuredLogEventsHandler, Depends(get_list_structured_log_events_handler)
    ],
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
    """List structured log backlog events with optional filters.

    Returns paginated list of structured log backlog events (Redis sorted set),
    with optional filtering by search text, user_id, event_type, and time range.

    Only accessible by superusers.
    """
    result = await handler.handle(
        ListStructuredLogEventsQuery(
            search=search,
            user_id=user_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )
    )
    items = [
        DomainEventSchema(
            id=item.id,
            event_type=item.event_type,
            event_data=item.event_data,
            stored_at=item.stored_at,
        )
        for item in result.items
    ]
    return DomainEventListResponse(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.websocket("/events/stream")
async def structured_log_events_stream(
    websocket: WebSocket,
    user: Annotated[UserEntity, Depends(get_current_superuser_from_token)],
    stream_gateway: Annotated[
        StructuredLogBacklogStreamGatewayProtocol,
        Depends(get_structured_log_backlog_stream_gateway),
    ],
) -> None:
    """WebSocket endpoint for real-time structured log backlog streaming.

    Streams new structured log backlog entries as they are emitted.
    Only accessible by superusers.
    """
    await websocket.accept()

    try:
        logger.info(f"Admin domain events WebSocket connected for superuser {user.id}")

        await websocket.send_json({"type": "connection_ack", "user_id": str(user.id)})

        async with stream_gateway.subscribe_to_stream() as subscription:
            receive_task = asyncio.create_task(_handle_client_messages_admin(websocket))
            stream_task = asyncio.create_task(_stream_events(websocket, subscription))

            done, pending = await asyncio.wait(
                [receive_task, stream_task], return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

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
    subscription: StructuredLogBacklogStreamSubscription,
) -> None:
    """Stream structured log backlog events from gateway to WebSocket."""
    while True:
        try:
            payload = await subscription.get_message(timeout=1.0)
            if payload:
                await websocket.send_json({"type": "domain_event", "data": payload})

        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Error streaming domain event: {e}")
            break
