"""WebSocket API route for real-time AuditLog events."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.core.utils.audit_log_serialization import deserialize_audit_log
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
            # Event streaming loop
            # The get_message(timeout=...) already provides backoff, no need for additional sleep
            while True:
                # Wait for AuditLog events from Redis with timeout
                # This blocks until a message arrives or timeout expires
                audit_log_message = await auditlog_subscription.get_message(timeout=1.0)

                if audit_log_message:
                    try:
                        # Deserialize using shared utility for consistency
                        audit_log_entity = deserialize_audit_log(audit_log_message)

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
                    except Exception as deserialize_error:
                        logger.error(
                            f"Failed to deserialize audit log message for user {user_id}: {deserialize_error}"
                        )
                        # Continue loop to avoid breaking the connection on bad messages

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
