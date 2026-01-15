"""Utilities for serializing and deserializing AuditLog entities for pub/sub messaging."""

from datetime import datetime
from typing import Any
from uuid import UUID

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain.entities import AuditLogEntity


def serialize_audit_log(audit_log: AuditLogEntity) -> dict[str, Any]:
    """Serialize an AuditLogEntity to a JSON-compatible dictionary for pub/sub.

    This ensures consistent serialization format across the application.
    UUIDs are converted to strings, datetimes to ISO format strings.

    Args:
        audit_log: The AuditLogEntity to serialize

    Returns:
        A JSON-compatible dictionary representation of the audit log
    """
    return dataclass_to_json_dict(audit_log)


def deserialize_audit_log(data: dict[str, Any]) -> AuditLogEntity:
    """Deserialize a dictionary to an AuditLogEntity.

    Handles conversion of:
    - String UUIDs back to UUID objects
    - ISO datetime strings back to datetime objects
    - Preserves None values for optional fields

    Args:
        data: Dictionary containing serialized audit log data

    Returns:
        An AuditLogEntity instance

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Convert string UUIDs back to UUID objects
    entity_id_raw = data.get("entity_id")
    return AuditLogEntity(
        id=UUID(data["id"]),
        user_id=UUID(data["user_id"]),
        activity_type=data["activity_type"],
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
        entity_id=UUID(entity_id_raw) if entity_id_raw else None,
        entity_type=data.get("entity_type"),
        meta=data.get("meta", {}),
    )
