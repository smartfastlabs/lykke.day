from datetime import UTC, datetime
from uuid import uuid4

from lykke.core.utils.audit_log_serialization import (
    deserialize_audit_log,
    serialize_audit_log,
)
from lykke.domain.entities import AuditLogEntity


def test_serialize_deserialize_audit_log_round_trip() -> None:
    user_id = uuid4()
    entity_id = uuid4()
    occurred_at = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    audit_log = AuditLogEntity(
        user_id=user_id,
        activity_type="TaskCompletedEvent",
        occurred_at=occurred_at,
        entity_id=entity_id,
        entity_type="task",
        meta={"entity_data": {"id": str(entity_id), "status": "COMPLETE"}},
    )

    serialized = serialize_audit_log(audit_log)

    assert serialized["id"] == str(audit_log.id)
    assert serialized["user_id"] == str(user_id)
    assert serialized["occurred_at"] == occurred_at.isoformat()
    assert serialized["entity_id"] == str(entity_id)
    assert serialized["meta"]["entity_data"]["status"] == "COMPLETE"

    deserialized = deserialize_audit_log(serialized)

    assert deserialized.id == audit_log.id
    assert deserialized.user_id == user_id
    assert deserialized.activity_type == audit_log.activity_type
    assert deserialized.occurred_at == occurred_at
    assert deserialized.entity_id == entity_id
    assert deserialized.entity_type == "task"
    assert deserialized.meta == audit_log.meta


def test_deserialize_audit_log_allows_missing_entity_id() -> None:
    user_id = uuid4()
    occurred_at = datetime(2025, 1, 2, 8, 30, tzinfo=UTC)
    data = {
        "id": str(uuid4()),
        "user_id": str(user_id),
        "activity_type": "MessageSentEvent",
        "occurred_at": occurred_at.isoformat(),
        "entity_id": None,
        "entity_type": None,
        "meta": {},
    }

    audit_log = deserialize_audit_log(data)

    assert audit_log.user_id == user_id
    assert audit_log.entity_id is None
    assert audit_log.entity_type is None
