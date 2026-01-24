"""Brain dump items table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class BrainDumpItem(Base):
    """Brain dump item table for storing captured entries."""

    __tablename__ = "brain_dump_items"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # BrainDumpItemStatus enum as string
    type = Column(String, nullable=False)  # BrainDumpItemType enum as string
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_brain_dump_items_date", "date"),
        Index("idx_brain_dump_items_user_id", "user_id"),
    )
