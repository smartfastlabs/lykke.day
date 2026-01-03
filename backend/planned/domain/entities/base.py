from dataclasses import dataclass, field, replace
from datetime import date as dt_date, datetime
from typing import Any, Self
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo


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


@dataclass(kw_only=True)
class BaseDateObject(BaseEntityObject):
    """Base class for entities that have a date associated with them.

    Entities can either implement _get_date() to return a date directly,
    or implement _get_datetime() and provide a timezone to convert to date.
    """

    timezone: str | None = field(default=None, repr=False)

    @property
    def date(self) -> dt_date:
        """Get the date for this entity.

        If _get_date() is implemented, it takes precedence.
        Otherwise, uses _get_datetime() with the configured timezone.
        """
        if v := self._get_date():
            return v
        dt = self._get_datetime()
        tz = self.timezone
        if tz:
            return dt.astimezone(ZoneInfo(tz)).date()
        # If no timezone set and datetime is timezone-aware, use its timezone
        if dt.tzinfo:
            return dt.date()
        # Fallback: assume UTC for naive datetimes
        return dt.date()

    def _get_datetime(self) -> datetime:
        raise NotImplementedError

    def _get_date(self) -> dt_date | None:
        return None
