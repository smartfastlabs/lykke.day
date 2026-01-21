"""Time block definitions table definition."""

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class TimeBlockDefinition(Base):
    """Time block definition table for storing reusable time block templates."""

    __tablename__ = "time_block_definitions"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)  # TimeBlockType enum as string
    category = Column(String, nullable=False)  # TimeBlockCategory enum as string

    __table_args__ = (Index("idx_time_block_definitions_user_id", "user_id"),)

