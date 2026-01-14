"""Chatbot WebSocket API route."""

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.presentation.api.schemas.websocket_message import (
    WebSocketAssistantMessageSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketMessageReceivedSchema,
    WebSocketUserMessageSchema,
)
from lykke.presentation.api.websocket import ConnectionState

from .dependencies.services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)
from .dependencies.user import get_current_user_from_token

router = APIRouter()


async def send_ws_message(websocket: WebSocket, message: dict) -> None:
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


async def generate_dummy_response(
    state: ConnectionState, user_message: MessageEntity
) -> MessageEntity | None:
    """Generate a dummy response (placeholder for LLM integration).

    Args:
        state: Connection state with cached entities
        user_message: The user's message

    Returns:
        An optional assistant message entity
    """
    # For now, return a simple canned response
    # In the future, this will be replaced with actual LLM integration
    import random

    if random.random() < 0.8:  # 80% chance of response
        return MessageEntity(
            conversation_id=state.conversation_id,
            role=value_objects.MessageRole.ASSISTANT,
            content=f"I received your message: '{user_message.content}'. This is a dummy response - LLM integration coming soon!",
        )

    return None


async def handle_user_message(
    websocket: WebSocket,
    state: ConnectionState,
    message_data: dict,
) -> None:
    """Handle incoming user message.

    Args:
        websocket: The WebSocket connection
        state: Connection state with cached entities
        message_data: Parsed message data from client
    """
    try:
        # Parse and validate message
        user_msg_schema = WebSocketUserMessageSchema(**message_data)

        # Create user message entity
        # Only pass id if client provided one (for idempotency)
        if user_msg_schema.message_id:
            user_message = MessageEntity(
                id=user_msg_schema.message_id,
                conversation_id=state.conversation_id,
                role=value_objects.MessageRole.USER,
                content=user_msg_schema.content,
            )
        else:
            user_message = MessageEntity(
                conversation_id=state.conversation_id,
                role=value_objects.MessageRole.USER,
                content=user_msg_schema.content,
            )

        # Persist user message
        async with state.new_uow() as uow:
            await uow.create(user_message)

            # Update conversation's last_message_at
            updated_conversation = state.conversation.update_last_message_time()
            uow.add(updated_conversation)
            state.conversation = updated_conversation  # Update cached conversation

        logger.info(f"Persisted user message {user_message.id}")

        # Send acknowledgment
        from lykke.presentation.api.schemas.mappers import map_message_to_schema

        ack = WebSocketMessageReceivedSchema(
            message=map_message_to_schema(user_message),
        )
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        # Generate assistant response
        assistant_message = await generate_dummy_response(state, user_message)

        if assistant_message:
            # Persist assistant message
            async with state.new_uow() as uow:
                await uow.create(assistant_message)

                # Update conversation timestamp again
                updated_conversation = state.conversation.update_last_message_time()
                uow.add(updated_conversation)
                state.conversation = updated_conversation

            logger.info(f"Persisted assistant message {assistant_message.id}")

            # Send complete assistant message
            assistant_msg_schema = WebSocketAssistantMessageSchema(
                message=map_message_to_schema(assistant_message),
            )
            await send_ws_message(
                websocket, assistant_msg_schema.model_dump(mode="json")
            )

    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        await send_error(websocket, "MESSAGE_ERROR", str(e))


@router.websocket("/conversations/{conversation_id}/ws")
async def chatbot_websocket(
    websocket: WebSocket,
    conversation_id: str,
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> None:
    """WebSocket endpoint for real-time chatbot communication.

    This endpoint:
    1. Accepts WebSocket connection
    2. Authenticates user
    3. Loads and caches conversation, bot personality, user
    4. Handles bidirectional message streaming
    5. Maintains connection state until disconnect

    Args:
        websocket: WebSocket connection
        conversation_id: UUID of the conversation
        uow_factory: Unit of work factory (injected)
        ro_repo_factory: Read-only repository factory (injected)
    """
    await websocket.accept()

    try:
        # Authenticate user from WebSocket query params or headers
        user = await get_current_user_from_token(websocket)

        # Create read-only repositories scoped to user
        ro_repos = ro_repo_factory.create(user.id)

        # Initialize connection state (loads all required entities)
        state = await ConnectionState.create(
            conversation_id=UUID(conversation_id),
            user=user,
            ro_repos=ro_repos,
            uow_factory=uow_factory,
        )

        logger.info(
            f"WebSocket connection established for user {user.id}, "
            f"conversation {conversation_id}"
        )

        # Send connection acknowledgment
        ack = WebSocketConnectionAckSchema(
            conversation_id=state.conversation_id,
            user_id=state.user_id,
            bot_personality_name=state.bot_personality.name,
        )
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Route based on message type
            msg_type = message_data.get("type")

            if msg_type == "user_message":
                await handle_user_message(websocket, state, message_data)
            else:
                await send_error(
                    websocket,
                    "UNKNOWN_MESSAGE_TYPE",
                    f"Unknown message type: {msg_type}",
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")

    except NotFoundError as e:
        logger.error(f"Not found error: {e}")
        await send_error(websocket, "NOT_FOUND", str(e))
        await websocket.close()

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await send_error(websocket, "INTERNAL_ERROR", "An unexpected error occurred")
        await websocket.close()
