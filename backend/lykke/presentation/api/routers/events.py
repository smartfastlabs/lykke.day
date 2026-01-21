"""WebSocket API route for real-time domain event broadcasts."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.core.utils.domain_event_serialization import deserialize_domain_event
from lykke.domain.events.base import AuditableDomainEvent
from lykke.presentation.api.schemas.websocket_message import (
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
    """WebSocket endpoint for real-time domain event broadcasts.

    This endpoint:
    1. Accepts WebSocket connection
    2. Authenticates user
    3. Subscribes to user's domain-events channel
    4. Filters events (only forwards AuditableDomainEvents to clients)
    5. Sends simplified event notifications

    Note: This is a simplified implementation that just logs auditable events.
    Full implementation would look up AuditLogEntity and send complete data.

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

        # Subscribe to user's domain-events channel (replaces old auditlog channel)
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="domain-events"
        ) as domain_events_subscription:
            # Event streaming loop
            while True:
                # Wait for domain events from Redis with timeout
                domain_event_message = await domain_events_subscription.get_message(
                    timeout=1.0
                )

                if domain_event_message:
                    try:
                        # Deserialize domain event
                        domain_event = deserialize_domain_event(domain_event_message)

                        # Filter: Only forward AuditableDomainEvents to clients
                        # This implements conservative filtering - only user-visible actions
                        if not isinstance(domain_event, AuditableDomainEvent):
                            logger.debug(
                                f"Filtered out non-auditable event {domain_event.__class__.__name__}"
                            )
                            continue

                        # TODO: Full implementation would:
                        # 1. Look up corresponding AuditLogEntity from database
                        # 2. Convert to WebSocketAuditLogEventSchema
                        # 3. Send to client
                        #
                        # For now, just log that we received an auditable event
                        logger.info(
                            f"Received AuditableDomainEvent {domain_event.__class__.__name__} "
                            f"for user {user_id} (WebSocket notification not yet fully implemented)"
                        )

                    except Exception as deserialize_error:
                        logger.error(
                            f"Failed to process domain event for user {user_id}: {deserialize_error}"
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
