"""Chatbot API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.chatbot import SendMessageHandler
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    SendMessageRequestSchema,
    SendMessageResponseSchema,
)
from lykke.presentation.api.schemas.mappers import map_message_to_schema

from .dependencies.commands.chatbot import get_send_message_handler
from .dependencies.user import get_current_user

router = APIRouter()


@router.post(
    "/conversations/{conversation_id}/messages", response_model=SendMessageResponseSchema
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    send_message_handler: Annotated[SendMessageHandler, Depends(get_send_message_handler)],
) -> SendMessageResponseSchema:
    """Send a message to a conversation and optionally receive a response.

    Args:
        conversation_id: The ID of the conversation
        request: The message request containing the content
        user: The current authenticated user
        send_message_handler: The injected send message handler

    Returns:
        SendMessageResponseSchema containing the user message and optional assistant response
    """
    user_message, assistant_message = await send_message_handler.run(
        conversation_id=UUID(conversation_id),
        content=request.content,
    )

    return SendMessageResponseSchema(
        user_message=map_message_to_schema(user_message),
        assistant_message=(
            map_message_to_schema(assistant_message) if assistant_message else None
        ),
    )
