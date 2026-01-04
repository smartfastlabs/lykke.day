from dataclasses import dataclass, field, replace
from typing import Any, Self
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class BaseObject:
    """Base class for all domain objects."""

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        # Exclude init=False fields from replace() call
        # These fields cannot be specified in replace() but we don't want to include them anyway
        from dataclasses import fields
        init_false_fields = {f.name for f in fields(self) if not f.init}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in init_false_fields}
        return replace(self, **filtered_kwargs)


@dataclass(kw_only=True)
class BaseEntityObject(BaseObject):
    id: UUID = field(default_factory=uuid4)


@dataclass(kw_only=True)
class BaseConfigObject(BaseEntityObject):
    pass
