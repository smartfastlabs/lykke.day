from typing import Any

from sqlalchemy import Select

from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity
from lykke.infrastructure.database.tables import tactics_tbl

from .base import UserScopedBaseRepository


class TacticRepository(UserScopedBaseRepository[TacticEntity, value_objects.TacticQuery]):
    Object = TacticEntity
    table = tactics_tbl
    QueryClass = value_objects.TacticQuery

    def build_query(self, query: value_objects.TacticQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.ids:
            stmt = stmt.where(self.table.c.id.in_(query.ids))

        if query.name:
            stmt = stmt.where(self.table.c.name == query.name)

        return stmt

    @staticmethod
    def entity_to_row(tactic: TacticEntity) -> dict[str, Any]:
        """Convert a Tactic entity to a database row dict."""
        return {
            "id": tactic.id,
            "user_id": tactic.user_id,
            "name": tactic.name,
            "description": tactic.description,
        }
