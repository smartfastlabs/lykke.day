"""Tests for AI chat domain events."""

from __future__ import annotations

from uuid import uuid4

from lykke.domain.events.ai_chat_events import MessageReceivedEvent, MessageSentEvent


def test_message_received_event_sets_entity_metadata() -> None:
    user_id = uuid4()
    message_id = uuid4()

    event = MessageReceivedEvent(
        user_id=user_id,
        message_id=message_id,
        role="user",
        content_preview="Hi there",
    )

    assert event.entity_id == message_id
    assert event.entity_type == "message"


def test_message_sent_event_sets_entity_metadata() -> None:
    user_id = uuid4()
    message_id = uuid4()

    event = MessageSentEvent(
        user_id=user_id,
        message_id=message_id,
        role="assistant",
        content_preview="Hello back",
    )

    assert event.entity_id == message_id
    assert event.entity_type == "message"
