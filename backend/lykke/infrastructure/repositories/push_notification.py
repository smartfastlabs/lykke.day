from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity
from lykke.infrastructure.database.tables import push_notifications_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
)

from .base import UserScopedBaseRepository


class PushNotificationRepository(
    UserScopedBaseRepository[
        PushNotificationEntity, value_objects.PushNotificationQuery
    ]
):
    Object = PushNotificationEntity
    table = push_notifications_tbl
    QueryClass = value_objects.PushNotificationQuery

    def build_query(self, query: value_objects.PushNotificationQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt: Select[tuple] = super().build_query(query)

        if query.push_subscription_id is not None:
            stmt = stmt.where(
                self.table.c.push_subscription_ids.any(query.push_subscription_id)
            )

        if query.status is not None:
            stmt = stmt.where(self.table.c.status == query.status)

        if query.sent_after is not None:
            stmt = stmt.where(self.table.c.sent_at > query.sent_after)

        if query.sent_before is not None:
            stmt = stmt.where(self.table.c.sent_at < query.sent_before)

        if query.message_hash is not None:
            stmt = stmt.where(self.table.c.message_hash == query.message_hash)

        if query.triggered_by is not None:
            stmt = stmt.where(self.table.c.triggered_by == query.triggered_by)

        if query.priority is not None:
            stmt = stmt.where(self.table.c.priority == query.priority)

        # Default ordering: most recent first (descending by sent_at)
        if not query.order_by:
            stmt = stmt.order_by(None).order_by(self.table.c.sent_at.desc())

        return stmt

    @staticmethod
    def entity_to_row(push_notification: PushNotificationEntity) -> dict[str, Any]:
        """Convert a PushNotification entity to a database row dict."""
        row: dict[str, Any] = {
            "id": push_notification.id,
            "user_id": push_notification.user_id,
            "push_subscription_ids": push_notification.push_subscription_ids,
            "content": push_notification.content,
            "status": push_notification.status,
            "error_message": push_notification.error_message,
            "sent_at": push_notification.sent_at,
            "message": push_notification.message,
            "priority": push_notification.priority,
            "message_hash": push_notification.message_hash,
            "triggered_by": push_notification.triggered_by,
            "llm_snapshot": dataclass_to_json_dict(push_notification.llm_snapshot)
            if push_notification.llm_snapshot
            else None,
        }

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> PushNotificationEntity:
        """Convert a database row dict to a PushNotification entity."""
        data = dict(row)

        llm_snapshot = data.get("llm_snapshot")
        if isinstance(llm_snapshot, dict):
            request_messages = llm_snapshot.pop("request_messages", None)
            request_tools = llm_snapshot.pop("request_tools", None)
            request_tool_choice = llm_snapshot.pop("request_tool_choice", None)
            request_model_params = llm_snapshot.pop("request_model_params", None)

            if "messages" not in llm_snapshot:
                llm_snapshot["messages"] = request_messages
            if "tools" not in llm_snapshot:
                llm_snapshot["tools"] = request_tools
            if "tool_choice" not in llm_snapshot:
                llm_snapshot["tool_choice"] = request_tool_choice
            if "model_params" not in llm_snapshot:
                llm_snapshot["model_params"] = request_model_params

            llm_snapshot.pop("tool_calls", None)
            llm_snapshot.pop("tool_results", None)
            llm_snapshot.pop("prompt_context", None)
            llm_snapshot.pop("context_prompt", None)
            llm_snapshot.pop("ask_prompt", None)
            llm_snapshot.pop("tools_prompt", None)

            referenced_entities = llm_snapshot.get("referenced_entities")
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
                llm_snapshot["referenced_entities"] = parsed_entities

            llm_provider = llm_snapshot.get("llm_provider")
            if isinstance(llm_provider, str):
                llm_snapshot["llm_provider"] = value_objects.LLMProvider(llm_provider)

            current_time = llm_snapshot.get("current_time")
            if isinstance(current_time, str):
                llm_snapshot["current_time"] = datetime.fromisoformat(current_time)

            data["llm_snapshot"] = value_objects.LLMRunResultSnapshot(
                **filter_init_false_fields(
                    llm_snapshot, value_objects.LLMRunResultSnapshot
                )
            )

        data = filter_init_false_fields(data, PushNotificationEntity)
        data = ensure_datetimes_utc(data, keys=("sent_at",))
        return PushNotificationEntity(**data)
