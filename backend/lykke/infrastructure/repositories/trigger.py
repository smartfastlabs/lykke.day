from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Select, delete, select

from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity, TriggerEntity
from lykke.infrastructure.database.tables import (
    tactics_tbl,
    trigger_tactics_tbl,
    triggers_tbl,
)

from .base import UserScopedBaseRepository


class TriggerRepository(
    UserScopedBaseRepository[TriggerEntity, value_objects.TriggerQuery]
):
    Object = TriggerEntity
    table = triggers_tbl
    QueryClass = value_objects.TriggerQuery

    def build_query(self, query: value_objects.TriggerQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.ids:
            stmt = stmt.where(self.table.c.id.in_(query.ids))

        if query.name:
            stmt = stmt.where(self.table.c.name == query.name)

        return stmt

    @staticmethod
    def entity_to_row(trigger: TriggerEntity) -> dict[str, Any]:
        """Convert a Trigger entity to a database row dict."""
        return {
            "id": trigger.id,
            "user_id": trigger.user_id,
            "name": trigger.name,
            "description": trigger.description,
        }

    async def list_tactics_for_trigger(self, trigger_id: UUID) -> list[TacticEntity]:
        """Return tactics linked to a trigger."""
        async with self._get_connection(for_write=False) as conn:
            stmt = (
                select(tactics_tbl)
                .join(
                    trigger_tactics_tbl,
                    trigger_tactics_tbl.c.tactic_id == tactics_tbl.c.id,
                )
                .where(trigger_tactics_tbl.c.trigger_id == trigger_id)
                .where(trigger_tactics_tbl.c.user_id == self.user_id)
            )
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            return [TacticEntity(**dict(row)) for row in rows]

    async def set_tactics_for_trigger(
        self, trigger_id: UUID, tactic_ids: list[UUID]
    ) -> None:
        """Replace all tactics linked to a trigger."""
        async with self._get_connection(for_write=True) as conn:
            delete_stmt = delete(trigger_tactics_tbl).where(
                trigger_tactics_tbl.c.trigger_id == trigger_id,
                trigger_tactics_tbl.c.user_id == self.user_id,
            )
            await conn.execute(delete_stmt)

            if not tactic_ids:
                return

            rows = [
                {
                    "id": uuid4(),
                    "user_id": self.user_id,
                    "trigger_id": trigger_id,
                    "tactic_id": tactic_id,
                }
                for tactic_id in tactic_ids
            ]
            await conn.execute(trigger_tactics_tbl.insert().values(rows))
