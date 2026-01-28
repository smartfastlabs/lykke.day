"""Factoid repository implementation."""

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity
from lykke.infrastructure.database.tables import factoids_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import UserScopedBaseRepository


class FactoidRepository(
    UserScopedBaseRepository[FactoidEntity, value_objects.FactoidQuery]
):
    """Repository for managing Factoid entities."""

    Object = FactoidEntity
    table = factoids_tbl
    QueryClass = value_objects.FactoidQuery

    def build_query(self, query: value_objects.FactoidQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add factoid-specific filtering
        if query.conversation_id is not None:
            stmt = stmt.where(self.table.c.conversation_id == query.conversation_id)

        if query.factoid_type is not None:
            stmt = stmt.where(self.table.c.factoid_type == query.factoid_type)

        if query.criticality is not None:
            stmt = stmt.where(self.table.c.criticality == query.criticality)

        # Filter for global vs conversation-specific factoids
        if query.is_global is not None:
            if query.is_global:
                stmt = stmt.where(self.table.c.conversation_id.is_(None))
            else:
                stmt = stmt.where(self.table.c.conversation_id.isnot(None))

        return stmt

    @staticmethod
    def entity_to_row(factoid: FactoidEntity) -> dict[str, Any]:
        """Convert a Factoid entity to a database row dict."""
        return {
            "id": factoid.id,
            "user_id": factoid.user_id,
            "conversation_id": factoid.conversation_id,
            "factoid_type": factoid.factoid_type.value,
            "criticality": factoid.criticality.value,
            "content": factoid.content,
            "embedding": factoid.embedding,
            "ai_suggested": "true" if factoid.ai_suggested else "false",
            "user_confirmed": "true" if factoid.user_confirmed else "false",
            "last_accessed": factoid.last_accessed,
            "access_count": factoid.access_count,
            "meta": factoid.meta,
            "created_at": factoid.created_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> FactoidEntity:
        """Convert a database row dict to a Factoid entity."""
        data = normalize_list_fields(dict(row), FactoidEntity)

        # Convert enum strings back to enums
        if "factoid_type" in data and isinstance(data["factoid_type"], str):
            data["factoid_type"] = value_objects.FactoidType(data["factoid_type"])
        if "criticality" in data and isinstance(data["criticality"], str):
            data["criticality"] = value_objects.FactoidCriticality(data["criticality"])

        # Convert string booleans back to booleans
        if "ai_suggested" in data and isinstance(data["ai_suggested"], str):
            data["ai_suggested"] = data["ai_suggested"].lower() == "true"
        if "user_confirmed" in data and isinstance(data["user_confirmed"], str):
            data["user_confirmed"] = data["user_confirmed"].lower() == "true"

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        # Ensure embedding defaults to None if not present
        if "embedding" not in data or data["embedding"] is None:
            data["embedding"] = None

        data = filter_init_false_fields(data, FactoidEntity)
        data = ensure_datetimes_utc(data, keys=("created_at", "last_accessed"))
        return FactoidEntity(**data)
