"""Schema description for generic data collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, cast

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class DataCollectionField:
    """Metadata for a collectable field."""

    name: str
    required: bool = False
    prompt: str | None = None
    max_attempts: int = 3


@dataclass(frozen=True, kw_only=True)
class DataCollectionSchema(Generic[T]):
    """Schema describing how to collect a dataclass type over multiple turns."""

    dataclass_type: type[T]
    fields: list[DataCollectionField] = field(default_factory=list)

    def required_field_names(self) -> set[str]:
        return {f.name for f in self.fields if f.required}

    def all_field_names(self) -> set[str]:
        if self.fields:
            return {f.name for f in self.fields}
        # If no explicit fields are provided, treat all dataclass fields as collectable.
        from dataclasses import fields as dataclass_fields

        return {f.name for f in dataclass_fields(cast("type[Any]", self.dataclass_type))}

