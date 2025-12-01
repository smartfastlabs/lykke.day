import uuid
from datetime import UTC, date as dt_date, datetime, time
from typing import Any, Self
from zoneinfo import ZoneInfo

import pydantic

from planned import settings


class BaseObject(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))
    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # frozen=True,
    )

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        return self.model_copy(update=kwargs)


class BaseDateObject(BaseObject):
    @pydantic.computed_field  # mypy: ignore
    @property
    def date(self) -> dt_date:
        if v := self._get_date():
            return v
        return self._get_datetime().astimezone(ZoneInfo(settings.TIMEZONE)).date()

    def _get_datetime(self) -> datetime:
        raise NotImplementedError

    def _get_date(self) -> dt_date | None:
        return None
