"""Message repository implementation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.infrastructure.database.tables import messages_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import UserScopedBaseRepository


class MessageRepository(
    UserScopedBaseRepository[MessageEntity, value_objects.MessageQuery]
):
    """Repository for managing user-scoped Message entities."""

    Object = MessageEntity
    table = messages_tbl
    QueryClass = value_objects.MessageQuery

    def build_query(self, query: value_objects.MessageQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add message-specific filtering
        if query.role is not None:
            stmt = stmt.where(self.table.c.role == query.role)

        return stmt

    @staticmethod
    def entity_to_row(message: MessageEntity) -> dict[str, Any]:
        """Convert a Message entity to a database row dict."""
        return {
            "id": message.id,
            "user_id": message.user_id,
            "role": message.role.value,
            "type": message.type.value,
            "content": message.content,
            "meta": message.meta,
            "llm_run_result": dataclass_to_json_dict(message.llm_run_result)
            if message.llm_run_result
            else None,
            "created_at": message.created_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> MessageEntity:
        """Convert a database row dict to a Message entity."""
        data = normalize_list_fields(dict(row), MessageEntity)

        # Convert enum strings back to enums
        if "role" in data and isinstance(data["role"], str):
            data["role"] = value_objects.MessageRole(data["role"])
        if "type" in data and isinstance(data["type"], str):
            data["type"] = value_objects.MessageType(data["type"])

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        llm_run_result = data.get("llm_run_result")
        if isinstance(llm_run_result, dict):
            tool_calls = llm_run_result.get("tool_calls")
            if tool_calls is None:
                tool_calls = llm_run_result.get("tool_results", [])
            if isinstance(tool_calls, list):
                tool_calls = [
                    value_objects.LLMToolCallResultSnapshot(
                        **filter_init_false_fields(
                            result, value_objects.LLMToolCallResultSnapshot
                        )
                    )
                    if isinstance(result, dict)
                    else result
                    for result in tool_calls
                ]
            llm_run_result["tool_calls"] = tool_calls
            llm_run_result.pop("tool_results", None)

            referenced_entities = llm_run_result.get("referenced_entities")
            if isinstance(referenced_entities, list):
                parsed_entities = []
                for entity in referenced_entities:
                    if isinstance(entity, dict):
                        entity_id = entity.get("entity_id")
                        if isinstance(entity_id, str):
                            entity["entity_id"] = UUID(entity_id)
                        parsed_entities.append(
                            value_objects.LLMReferencedEntitySnapshot(
                                **filter_init_false_fields(
                                    entity, value_objects.LLMReferencedEntitySnapshot
                                )
                            )
                        )
                    else:
                        parsed_entities.append(entity)
                llm_run_result["referenced_entities"] = parsed_entities

            llm_provider = llm_run_result.get("llm_provider")
            if isinstance(llm_provider, str):
                llm_run_result["llm_provider"] = value_objects.LLMProvider(llm_provider)

            current_time = llm_run_result.get("current_time")
            if isinstance(current_time, str):
                llm_run_result["current_time"] = datetime.fromisoformat(current_time)

            data["llm_run_result"] = value_objects.LLMRunResultSnapshot(
                **filter_init_false_fields(
                    llm_run_result, value_objects.LLMRunResultSnapshot
                )
            )

        data = filter_init_false_fields(data, MessageEntity)
        data = ensure_datetimes_utc(data, keys=("created_at",))
        return MessageEntity(**data)
