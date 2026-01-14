"""AuditLog repository implementation."""

from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity
from lykke.infrastructure.database.tables import audit_logs_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc
from sqlalchemy.sql import Select

from .base import UserScopedBaseRepository


class AuditLogRepository(
    UserScopedBaseRepository[AuditLogEntity, value_objects.AuditLogQuery]
):
    """Repository for managing AuditLog entities."""

    Object = AuditLogEntity
    table = audit_logs_tbl
    QueryClass = value_objects.AuditLogQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize AuditLogRepository with user scoping."""
        super().__init__(user_id=user_id)

    def build_query(self, query: value_objects.AuditLogQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        from sqlalchemy import select

        # Build base query with user scoping
        stmt: Select[tuple] = select(self.table)
        stmt = self._apply_user_scope(stmt)

        # Apply pagination
        if query.limit is not None:
            stmt = stmt.limit(query.limit)

        if query.offset:
            stmt = stmt.offset(query.offset)

        # Add audit log-specific filtering
        if query.activity_type is not None:
            stmt = stmt.where(
                self.table.c.activity_type == query.activity_type.value
            )

        if query.entity_id is not None:
            stmt = stmt.where(self.table.c.entity_id == query.entity_id)

        if query.entity_type is not None:
            stmt = stmt.where(self.table.c.entity_type == query.entity_type)

        # Handle occurred_at filtering (use occurred_at instead of created_at)
        if query.occurred_after is not None:
            stmt = stmt.where(self.table.c.occurred_at > query.occurred_after)

        if query.occurred_before is not None:
            stmt = stmt.where(self.table.c.occurred_at < query.occurred_before)

        # Handle ordering - default to occurred_at descending (most recent first)
        if query.order_by:
            col = getattr(self.table.c, query.order_by, None)
            if col is not None:
                if query.order_by_desc:
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col)
        else:
            # Default ordering by occurred_at descending (most recent first)
            stmt = stmt.order_by(self.table.c.occurred_at.desc())

        return stmt

    @staticmethod
    def entity_to_row(audit_log: AuditLogEntity) -> dict[str, Any]:
        """Convert an AuditLog entity to a database row dict."""
        row: dict[str, Any] = {
            "id": audit_log.id,
            "user_id": audit_log.user_id,
            "activity_type": audit_log.activity_type.value,
            "occurred_at": audit_log.occurred_at,
            "entity_id": audit_log.entity_id,
            "entity_type": audit_log.entity_type,
        }

        # Handle JSONB meta field
        if audit_log.meta:
            row["meta"] = audit_log.meta
        else:
            row["meta"] = None

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> AuditLogEntity:
        """Convert a database row dict to an AuditLog entity."""
        from lykke.infrastructure.repositories.base.utils import (
            filter_init_false_fields,
            normalize_list_fields,
        )

        data = normalize_list_fields(dict(row), AuditLogEntity)

        # Convert enum string back to enum
        if "activity_type" in data and isinstance(data["activity_type"], str):
            data["activity_type"] = value_objects.ActivityType(data["activity_type"])

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        data = filter_init_false_fields(data, AuditLogEntity)
        data = ensure_datetimes_utc(data, keys=("occurred_at",))
        return AuditLogEntity(**data)
