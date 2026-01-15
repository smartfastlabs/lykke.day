"""AuditLog repository implementation."""

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity
from lykke.infrastructure.database.tables import audit_logs_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc

from .base import UserScopedBaseRepository


class AuditLogRepository(
    UserScopedBaseRepository[AuditLogEntity, value_objects.AuditLogQuery]
):
    """Repository for managing AuditLog entities."""

    Object = AuditLogEntity
    table = audit_logs_tbl
    QueryClass = value_objects.AuditLogQuery

    def build_query(self, query: value_objects.AuditLogQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""

        stmt: Select[tuple] = super().build_query(query)

        # Add audit log-specific filtering
        if query.activity_type is not None:
            stmt = stmt.where(self.table.c.activity_type == query.activity_type)

        if query.entity_id is not None:
            stmt = stmt.where(self.table.c.entity_id == query.entity_id)

        if query.entity_type is not None:
            stmt = stmt.where(self.table.c.entity_type == query.entity_type)

        # Handle occurred_at filtering (use occurred_at instead of created_at)
        if query.occurred_after is not None:
            stmt = stmt.where(self.table.c.occurred_at > query.occurred_after)

        if query.occurred_before is not None:
            stmt = stmt.where(self.table.c.occurred_at < query.occurred_before)

        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        # Default ordering: most recent first (descending by occurred_at)
        # Override any default ordering from base class
        if not query.order_by:
            # Clear any existing ordering and apply default for audit logs
            stmt = stmt.order_by(None).order_by(self.table.c.occurred_at.desc())
        # If query.order_by is set, base class will handle it

        return stmt

    @staticmethod
    def entity_to_row(audit_log: AuditLogEntity) -> dict[str, Any]:
        """Convert an AuditLog entity to a database row dict."""
        row: dict[str, Any] = {
            "id": audit_log.id,
            "user_id": audit_log.user_id,
            "activity_type": audit_log.activity_type,
            "occurred_at": audit_log.occurred_at,
            "date": audit_log.date,
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

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        data = filter_init_false_fields(data, AuditLogEntity)
        data = ensure_datetimes_utc(data, keys=("occurred_at",))
        return AuditLogEntity(**data)
