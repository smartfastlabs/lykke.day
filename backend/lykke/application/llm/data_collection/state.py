"""State machine for multi-turn data collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast

from lykke.core.exceptions import DomainError

from .schema import DataCollectionSchema


class DataCollectionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass(kw_only=True)
class DataCollectionState:
    """Serializable state for a multi-turn collection workflow.

    This is designed to be persisted in `UseCaseConfigEntity.config`.
    """

    version: int = 1
    status: DataCollectionStatus = DataCollectionStatus.ACTIVE
    collected: dict[str, Any] = field(default_factory=dict)
    asked: dict[str, dict[str, Any]] = field(default_factory=dict)  # field -> metadata
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "DataCollectionState":
        if raw is None:
            return cls()
        status_raw = raw.get("status", DataCollectionStatus.ACTIVE.value)
        try:
            status = DataCollectionStatus(status_raw)
        except ValueError:
            status = DataCollectionStatus.ACTIVE
        completed_at_raw = raw.get("completed_at")
        completed_at = None
        if isinstance(completed_at_raw, str):
            try:
                completed_at = datetime.fromisoformat(completed_at_raw)
            except ValueError:
                completed_at = None
        asked_raw = raw.get("asked")
        asked = cast("dict[str, dict[str, Any]]", asked_raw) if isinstance(asked_raw, dict) else {}
        collected_raw = raw.get("collected")
        collected = cast("dict[str, Any]", collected_raw) if isinstance(collected_raw, dict) else {}
        started_at_raw = raw.get("started_at")
        started_at = datetime.now(UTC)
        if isinstance(started_at_raw, str):
            try:
                started_at = datetime.fromisoformat(started_at_raw)
            except ValueError:
                started_at = datetime.now(UTC)
        version_raw = raw.get("version", 1)
        version = int(version_raw) if isinstance(version_raw, int | str) else 1
        return cls(
            version=version,
            status=status,
            collected=dict(collected),
            asked=dict(asked),
            started_at=started_at,
            completed_at=completed_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status.value,
            "collected": dict(self.collected),
            "asked": dict(self.asked),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def ensure_active(self) -> None:
        if self.status != DataCollectionStatus.ACTIVE:
            raise DomainError(f"Collection is {self.status.value}, not active")

    def mark_completed(self) -> "DataCollectionState":
        if self.status == DataCollectionStatus.COMPLETED:
            return self
        return self.clone(
            status=DataCollectionStatus.COMPLETED,
            completed_at=datetime.now(UTC),
        )

    def abort(self) -> "DataCollectionState":
        if self.status == DataCollectionStatus.ABORTED:
            return self
        return self.clone(status=DataCollectionStatus.ABORTED)

    def missing_required_fields(self, schema: DataCollectionSchema[Any]) -> list[str]:
        missing = []
        for name in sorted(schema.required_field_names()):
            val = self.collected.get(name)
            if val is None or val == "" or val == []:
                missing.append(name)
        return missing

    def record_asked(self, field_name: str) -> "DataCollectionState":
        meta = dict(self.asked.get(field_name, {}))
        attempts = meta.get("attempts", 0)
        meta["attempts"] = int(attempts) + 1
        meta["asked_at"] = datetime.now(UTC).isoformat()
        updated = dict(self.asked)
        updated[field_name] = meta
        return self.clone(asked=updated)

    def merge_collected(self, updates: dict[str, Any]) -> "DataCollectionState":
        self.ensure_active()
        merged = dict(self.collected)
        for k, v in updates.items():
            merged[k] = v
        return self.clone(collected=merged)

    def clone(self, **kwargs: Any) -> "DataCollectionState":
        from dataclasses import replace

        return replace(self, **kwargs)

