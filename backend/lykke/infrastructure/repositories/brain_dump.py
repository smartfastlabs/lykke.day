from datetime import datetime
from typing import Any

from sqlalchemy.sql import Select

from lykke.core.utils.encryption import decrypt_text, encrypt_text
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity
from lykke.infrastructure.database.tables import brain_dumps_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
)

from .base import UserScopedBaseRepository


class BrainDumpRepository(
    UserScopedBaseRepository[BrainDumpEntity, value_objects.BrainDumpQuery]
):
    Object = BrainDumpEntity
    table = brain_dumps_tbl
    QueryClass = value_objects.BrainDumpQuery

    @staticmethod
    def entity_to_row(item: BrainDumpEntity) -> dict[str, Any]:
        """Convert a BrainDump entity to a database row dict."""
        return {
            "id": item.id,
            "user_id": item.user_id,
            "date": item.date,
            "text": encrypt_text(item.text),
            "status": item.status.value,
            "type": item.type.value,
            "llm_run_result": dataclass_to_json_dict(item.llm_run_result)
            if item.llm_run_result
            else None,
            "created_at": item.created_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> BrainDumpEntity:
        """Convert a database row dict to a BrainDump entity."""
        data = filter_init_false_fields(dict(row), BrainDumpEntity)

        status = data.get("status")
        if isinstance(status, str):
            data["status"] = value_objects.BrainDumpItemStatus(status)

        item_type = data.get("type")
        if isinstance(item_type, str):
            data["type"] = value_objects.BrainDumpItemType(item_type)

        text = data.get("text")
        if isinstance(text, str):
            data["text"] = decrypt_text(text)

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

        data = ensure_datetimes_utc(data, keys=("created_at",))
        return BrainDumpEntity(**data)

    def build_query(self, query: value_objects.BrainDumpQuery) -> Select[tuple]:
        """Build a SQLAlchemy query with brain dump filters."""
        stmt = super().build_query(query)

        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        if query.status is not None:
            stmt = stmt.where(self.table.c.status == query.status.value)

        if query.type is not None:
            stmt = stmt.where(self.table.c.type == query.type.value)

        return stmt
