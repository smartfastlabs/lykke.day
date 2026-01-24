"""Repository for UseCaseConfig entities."""

import json
from typing import Any

from sqlalchemy.sql import Select

from lykke.domain.entities.usecase_config import UseCaseConfigEntity
from lykke.infrastructure.database.tables import usecase_configs_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc

from .base import UseCaseConfigQuery, UserScopedBaseRepository


class UseCaseConfigRepository(
    UserScopedBaseRepository[UseCaseConfigEntity, UseCaseConfigQuery]
):
    Object = UseCaseConfigEntity
    table = usecase_configs_tbl
    QueryClass = UseCaseConfigQuery

    def build_query(self, query: UseCaseConfigQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.usecase is not None:
            stmt = stmt.where(self.table.c.usecase == query.usecase)

        return stmt

    @staticmethod
    def entity_to_row(config: UseCaseConfigEntity) -> dict[str, Any]:
        """Convert a UseCaseConfig entity to a database row dict."""
        # Ensure config is a dict (JSONB fields need to be JSON-serializable)
        config_dict = config.config if isinstance(config.config, dict) else {}
        return {
            "id": config.id,
            "user_id": config.user_id,
            "usecase": config.usecase,
            "config": config_dict,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> UseCaseConfigEntity:
        """Convert a database row dict to a UseCaseConfig entity."""
        data = dict(row)

        # Handle config - ensure it's a dict
        if "config" in data:
            if isinstance(data["config"], str):
                data["config"] = json.loads(data["config"])
            elif data["config"] is None:
                data["config"] = {}

        data = ensure_datetimes_utc(data, keys=("created_at", "updated_at"))
        return UseCaseConfigEntity(**data)
