"""Shared SQLAlchemy table mixins."""

from sqlalchemy import Column, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID


class HasDateMixin:
    """Add day-scoped date and day_id columns to a table."""

    date = Column(Date, nullable=False)
    day_id = Column(PGUUID, nullable=False)
