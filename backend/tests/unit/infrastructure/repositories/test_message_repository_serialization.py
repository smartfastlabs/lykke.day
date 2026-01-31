"""Unit tests for MessageRepository serialization (no DB required)."""

from datetime import UTC, datetime
from uuid import uuid4

from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.infrastructure.repositories.message import MessageRepository


def test_message_repository_roundtrip_type_and_llm_run_result() -> None:
    repo = MessageRepository(user_id=uuid4())
    user_id = uuid4()

    message = MessageEntity(
        id=uuid4(),
        user_id=user_id,
        role=value_objects.MessageRole.ASSISTANT,
        type=value_objects.MessageType.SMS_OUTBOUND,
        content="ok",
        llm_run_result=value_objects.LLMRunResultSnapshot(
            tool_calls=[
                value_objects.LLMToolCallResultSnapshot(
                    tool_name="reply",
                    arguments={"message": "ok"},
                    result=None,
                )
            ],
            prompt_context={"k": "v"},
            current_time=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            llm_provider=value_objects.LLMProvider.ANTHROPIC,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
            tools_prompt="tools",
            referenced_entities=[
                value_objects.LLMReferencedEntitySnapshot(
                    entity_type="task",
                    entity_id=uuid4(),
                )
            ],
        ),
        created_at=datetime(2025, 1, 1, 12, 1, 0, tzinfo=UTC),
    )

    row = repo.entity_to_row(message)
    restored = repo.row_to_entity(row)

    assert restored.type == value_objects.MessageType.SMS_OUTBOUND
    assert restored.llm_run_result is not None
    assert restored.llm_run_result.llm_provider == value_objects.LLMProvider.ANTHROPIC
    assert restored.llm_run_result.tool_calls[0].tool_name == "reply"
    assert restored.llm_run_result.referenced_entities
