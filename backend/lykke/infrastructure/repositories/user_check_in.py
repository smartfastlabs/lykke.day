"""UserCheckIn repository implementation."""

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity
from lykke.infrastructure.database.tables import user_check_ins_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
)

from .base import UserScopedBaseRepository


class UserCheckInRepository(
    UserScopedBaseRepository[UserCheckInEntity, value_objects.UserCheckInQuery]
):
    Object = UserCheckInEntity
    table = user_check_ins_tbl
    QueryClass = value_objects.UserCheckInQuery

    @staticmethod
    def entity_to_row(entity: UserCheckInEntity) -> dict[str, Any]:
        """Convert a UserCheckIn entity to a database row dict."""
        row: dict[str, Any] = {
            "id": entity.id,
            "user_id": entity.user_id,
            "source": entity.source.value,
            "source_name": entity.source_name,
            "source_metadata": entity.source_metadata if entity.source_metadata else None,
            "checkin_at": entity.checkin_at,
            "created_at": entity.created_at,
            "text": entity.text,
            "scores": entity.scores if entity.scores else None,
        }
        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> UserCheckInEntity:
        """Convert a database row dict to a UserCheckIn entity."""
        data = filter_init_false_fields(dict(row), UserCheckInEntity)
        source = data.get("source")
        if isinstance(source, str):
            data["source"] = value_objects.UserCheckInSource(source)
        if data.get("source_metadata") is None:
            data["source_metadata"] = {}
        if data.get("scores") is None:
            data["scores"] = {}
        data = ensure_datetimes_utc(data, keys=("checkin_at", "created_at"))
        return UserCheckInEntity(**data)

    def build_query(self, query: value_objects.UserCheckInQuery) -> Select[tuple]:
        """Build SQLAlchemy select with user check-in filters."""
        stmt = super().build_query(query)
        if query.checkin_at_after is not None:
            stmt = stmt.where(self.table.c.checkin_at >= query.checkin_at_after)
        if query.checkin_at_before is not None:
            stmt = stmt.where(self.table.c.checkin_at <= query.checkin_at_before)
        if query.source is not None:
            stmt = stmt.where(self.table.c.source == query.source)
        if query.source_name is not None:
            stmt = stmt.where(self.table.c.source_name == query.source_name)
        return stmt
