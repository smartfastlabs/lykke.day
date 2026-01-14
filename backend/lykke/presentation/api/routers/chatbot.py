"""WebSocket API route for real-time AuditLog events."""

import asyncio
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.presentation.api.schemas.mappers import (
    map_audit_log_to_schema,
    map_message_to_schema,
)
from lykke.presentation.api.schemas.websocket_message import (
    WebSocketAuditLogEventSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketMessageEventSchema,
    WebSocketUserMessageSchema,
)

from .dependencies.services import (
    get_pubsub_gateway,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)
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


async def handle_user_message(
    message_data: dict[str, Any],
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    pubsub_gateway: PubSubGatewayProtocol,
    user_id: Any,
) -> None:
    """Handle incoming user message.

    Args:
        message_data: Parsed message data from client
        uow_factory: Unit of work factory
        ro_repo_factory: Read-only repository factory
        pubsub_gateway: PubSub gateway for publishing messages
        user_id: User ID
    """
    try:
        # Parse and validate message
        user_msg_schema = WebSocketUserMessageSchema(**message_data)

        # Create read-only repositories scoped to user
        ro_repos = ro_repo_factory.create(user_id)

        # Load conversation to verify it exists and belongs to user
        conversation = await ro_repos.conversation_ro_repo.get(
            user_msg_schema.conversation_id
        )

        # Create user message entity
        # Only pass id if client provided one (for idempotency)
        if user_msg_schema.message_id:
            user_message = MessageEntity(
                id=user_msg_schema.message_id,
                conversation_id=conversation.id,
                role=value_objects.MessageRole.USER,
                content=user_msg_schema.content,
            )
        else:
            user_message = MessageEntity(
                conversation_id=conversation.id,
                role=value_objects.MessageRole.USER,
                content=user_msg_schema.content,
            )

        # Persist user message
        async with uow_factory.create(user_id) as uow:
            await uow.create(user_message)

            # Update conversation's last_message_at
            updated_conversation = conversation.update_last_message_time()
            uow.add(updated_conversation)

        logger.info(
            f"Persisted user message {user_message.id} for conversation {conversation.id}"
        )

        # Publish message to messages channel
        message_schema = map_message_to_schema(user_message)
        await pubsub_gateway.publish_to_user_channel(
            user_id=user_id,
            channel_type="messages",
            message=message_schema.model_dump(mode="json"),
        )

        logger.debug(f"Published message {user_message.id} to messages channel")

        # No immediate response - the assistant will generate a response asynchronously
        # which will be sent via the messages pubsub channel

    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        raise


@router.websocket("/ws")
async def unified_websocket(
    websocket: WebSocket,
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
) -> None:
    """WebSocket endpoint for real-time events.

    This endpoint:
    1. Accepts WebSocket connection
    2. Authenticates user
    3. Subscribes to user's AuditLog and Messages channels
    4. Forwards all events to the client
    5. Accepts incoming messages and processes them asynchronously

    Args:
        websocket: WebSocket connection
        uow_factory: Unit of work factory (injected)
        ro_repo_factory: Read-only repository factory (injected)
        pubsub_gateway: PubSub gateway for subscribing to events (injected)
    """
    await websocket.accept()

    try:
        # Authenticate user from WebSocket query params or headers
        user = await get_current_user_from_token(websocket)
        user_id = user.id

        logger.info(f"WebSocket connection established for user {user_id}")

        # Send connection acknowledgment
        ack = WebSocketConnectionAckSchema(user_id=user_id)
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        # Subscribe to both user's AuditLog and Messages channels
        async with (
            pubsub_gateway.subscribe_to_user_channel(
                user_id=user_id, channel_type="auditlog"
            ) as auditlog_subscription,
            pubsub_gateway.subscribe_to_user_channel(
                user_id=user_id, channel_type="messages"
            ) as messages_subscription,
        ):
            # Give subscriptions a moment to be ready
            await asyncio.sleep(0.1)

            # Bidirectional message loop
            while True:
                # Non-blocking check for AuditLog events from Redis
                audit_log_message = await auditlog_subscription.get_message(timeout=0.1)

                if audit_log_message:
                    # Convert the AuditLog dict to schema and send to client
                    from datetime import datetime
                    from uuid import UUID

                    from lykke.domain.entities import AuditLogEntity

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

                # Non-blocking check for Message events from Redis
                message_event = await messages_subscription.get_message(timeout=0.1)

                if message_event:
                    # Convert the message dict to schema and send to client
                    from lykke.presentation.api.schemas.message import MessageSchema

                    # The message from Redis is already in schema format
                    message_schema = MessageSchema(**message_event)
                    message_event_schema = WebSocketMessageEventSchema(
                        message=message_schema
                    )

                    await send_ws_message(
                        websocket, message_event_schema.model_dump(mode="json")
                    )
                    logger.debug(
                        f"Sent Message event {message_schema.id} to user {user_id}"
                    )

                # Non-blocking check for WebSocket messages from client
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    message_data = json.loads(data)

                    # Route based on message type
                    msg_type = message_data.get("type")

                    if msg_type == "user_message":
                        # Process message asynchronously (don't wait for response)
                        await handle_user_message(
                            message_data,
                            uow_factory,
                            ro_repo_factory,
                            pubsub_gateway,
                            user_id,
                        )
                    else:
                        await send_error(
                            websocket,
                            "UNKNOWN_MESSAGE_TYPE",
                            f"Unknown message type: {msg_type}",
                        )

                except TimeoutError:
                    # No message from client, continue loop
                    pass

    except WebSocketDisconnect:
        logger.info(
            f"WebSocket disconnected for user {user.id if 'user' in locals() else 'unknown'}"
        )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await send_error(
                websocket, "INTERNAL_ERROR", "An unexpected error occurred"
            )
            await websocket.close()
        except Exception:
            # Connection may already be closed
            pass
