from typing import Any

from sqlalchemy.sql import Select

from lykke.core.utils.encryption import decrypt_text, encrypt_text
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
