"""WebSocket API route for real-time AuditLog events."""

import asyncio
import json
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.domain.entities import AuditLogEntity
from lykke.presentation.api.schemas.mappers import map_audit_log_to_schema
from lykke.presentation.api.schemas.websocket_message import (
    WebSocketAuditLogEventSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
)

from .dependencies.services import get_pubsub_gateway
from .dependencies.user import get_current_user_from_token

router = APIRouter()


async def send_ws_message(websocket: WebSocket, message: dict[str, Any]) -> None:
    """Send a JSON message over WebSocket.

    Args:
        websocket: The WebSocket connection
        message: Dictionary to send as JSON
    """
    await websocket.send_text(json.dumps(message))


async def send_error(websocket: WebSocket, code: str, message: str) -> None:
    """Send an error message over WebSocket.

    Args:
        websocket: The WebSocket connection
        code: Error code
        message: Error message
    """
    error_schema = WebSocketErrorSchema(code=code, message=message)
    await send_ws_message(websocket, error_schema.model_dump(mode="json"))


@router.websocket("/ws")
async def events_websocket(
    websocket: WebSocket,
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
) -> None:
    """WebSocket endpoint for real-time AuditLog events.

    This endpoint:
    1. Accepts WebSocket connection
    2. Authenticates user
    3. Subscribes to user's AuditLog channel
    4. Forwards all audit log events to the client

    Args:
        websocket: WebSocket connection
        pubsub_gateway: PubSub gateway for subscribing to events (injected)
    """
    await websocket.accept()

    try:
        # Authenticate user from WebSocket query params or headers
        try:
            user = await get_current_user_from_token(websocket)
            user_id = user.id
        except Exception as auth_error:
            logger.warning(f"Authentication failed for WebSocket: {auth_error}")
            await send_error(
                websocket,
                "AUTHENTICATION_ERROR",
                f"Authentication failed: {auth_error!s}",
            )
            await websocket.close(code=1008, reason="Authentication failed")
            return

        logger.info(f"Events WebSocket connection established for user {user_id}")

        # Send connection acknowledgment
        ack = WebSocketConnectionAckSchema(user_id=user_id)
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        # Subscribe to user's AuditLog channel
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="auditlog"
        ) as auditlog_subscription:
            # Give subscription a moment to be ready
            await asyncio.sleep(0.1)

            # Event streaming loop
            while True:
                # Non-blocking check for AuditLog events from Redis
                audit_log_message = await auditlog_subscription.get_message(timeout=0.1)

                if audit_log_message:
                    # Reconstruct the AuditLogEntity from the dict
                    # Note: Redis pub/sub serializes UUIDs to strings and datetimes to ISO strings
                    entity_id_raw = audit_log_message.get("entity_id")
                    audit_log_entity = AuditLogEntity(
                        id=UUID(audit_log_message["id"]),
                        user_id=UUID(audit_log_message["user_id"]),
                        activity_type=audit_log_message["activity_type"],
                        occurred_at=datetime.fromisoformat(
                            audit_log_message["occurred_at"]
                        ),
                        entity_id=UUID(entity_id_raw) if entity_id_raw else None,
                        entity_type=audit_log_message.get("entity_type"),
                        meta=audit_log_message.get("meta", {}),
                    )

                    # Convert to schema
                    audit_log_schema = map_audit_log_to_schema(audit_log_entity)
                    event_schema = WebSocketAuditLogEventSchema(
                        audit_log=audit_log_schema
                    )

                    await send_ws_message(
                        websocket, event_schema.model_dump(mode="json")
                    )
                    logger.debug(
                        f"Sent AuditLog event {audit_log_entity.id} to user {user_id}"
                    )

                # Small sleep to prevent tight loop
                await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info(
            f"Events WebSocket disconnected for user {user.id if 'user' in locals() else 'unknown'}"
        )

    except Exception as e:
        logger.error(f"Events WebSocket error: {e}")
        try:
            await send_error(
                websocket, "INTERNAL_ERROR", "An unexpected error occurred"
            )
            await websocket.close()
        except Exception:
            # Connection may already be closed
            pass
