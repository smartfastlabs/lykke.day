"""SMS login code repository - not user-scoped, manages verification codes."""

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import SmsLoginCodeEntity
from lykke.domain.entities.sms_login_code import _SYSTEM_USER_ID
from lykke.infrastructure.database.tables import sms_login_codes_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc

from .base import BaseRepository


class SmsLoginCodeRepository(
    BaseRepository[SmsLoginCodeEntity, value_objects.SmsLoginCodeQuery]
):
    """Repository for SMS login codes. Not user-scoped."""

    Object = SmsLoginCodeEntity
    table = sms_login_codes_tbl
    QueryClass = value_objects.SmsLoginCodeQuery

    def __init__(self) -> None:
        super().__init__()

    def build_query(self, query: value_objects.SmsLoginCodeQuery) -> Select[tuple]:
        """Build query for SMS login codes."""
        stmt = super().build_query(query)
        if query.phone_number is not None:
            stmt = stmt.where(self.table.c.phone_number == query.phone_number)
        if query.consumed is False:
            stmt = stmt.where(self.table.c.consumed_at.is_(None))
        if query.order_by is None:
            stmt = stmt.order_by(self.table.c.created_at.desc())
        return stmt

    @staticmethod
    def entity_to_row(entity: SmsLoginCodeEntity) -> dict[str, Any]:
        """Convert entity to database row."""
        return {
            "id": entity.id,
            "phone_number": entity.phone_number,
            "code_hash": entity.code_hash,
            "expires_at": entity.expires_at,
            "consumed_at": entity.consumed_at,
            "created_at": entity.created_at,
            "attempt_count": entity.attempt_count,
            "last_attempt_at": entity.last_attempt_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> SmsLoginCodeEntity:
        """Convert database row to entity."""
        data = dict(row)
        data = ensure_datetimes_utc(
            data, keys=("expires_at", "consumed_at", "created_at", "last_attempt_at")
        )
        data["user_id"] = _SYSTEM_USER_ID
        return SmsLoginCodeEntity(**data)

