"""Base schema classes."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
        },
    )


class BaseEntitySchema(BaseSchema):
    """Base schema for entities with ID."""

    id: UUID


class BaseDateSchema(BaseEntitySchema):
    """Base schema for entities with a date."""

    date: date

