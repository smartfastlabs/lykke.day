"""Query objects for building flexible queries with pagination, ordering, and filtering."""

from __future__ import annotations

from datetime import date as dt_date, datetime

import pydantic


class BaseQuery(pydantic.BaseModel):
    """Base query class for building flexible queries with pagination, ordering, and filtering."""

    limit: int | None = None
    offset: int | None = None
    order_by: str | None = None
    order_by_desc: bool | None = None
    created_before: datetime | None = None
    created_after: datetime | None = None

    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class DateQuery(BaseQuery):
    """Query class for entities with a date column."""

    date: dt_date | None = None

