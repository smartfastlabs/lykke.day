"""Messages table definition."""

from sqlalchemy import Column, Date, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Message(Base):
    """Message table for storing chat messages."""

    __tablename__ = "messages"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    date = Column(Date, nullable=False)  # extracted from sent_at for querying
    author = Column(String, nullable=False)  # Literal["system", "agent", "user"]
    sent_at = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    read_at = Column(DateTime)

    __table_args__ = (
        Index("idx_messages_date", "date"),
        Index("idx_messages_user_id", "user_id"),
    )

