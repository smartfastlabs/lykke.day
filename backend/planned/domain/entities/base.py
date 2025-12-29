from datetime import date as dt_date, datetime
from typing import Any, Self
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pydantic


class BaseObject(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # frozen=True,
    )

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        return self.model_copy(update=kwargs)


class BaseEntityObject(BaseObject):
    uuid: UUID = pydantic.Field(default_factory=uuid4)


class BaseConfigObject(BaseEntityObject):
    pass


class BaseDateObject(BaseEntityObject):
    """Base class for entities that have a date associated with them.

    Entities can either implement _get_date() to return a date directly,
    or implement _get_datetime() and provide a timezone to convert to date.
    """

    timezone: str | None = pydantic.Field(default=None, exclude=True)

    @pydantic.computed_field  # mypy: ignore
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
