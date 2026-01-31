"""SMS login codes table for one-time verification codes."""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class SmsLoginCode(Base):
    """SMS login code table for storing hashed verification codes."""

    __tablename__ = "sms_login_codes"

    id = Column(PGUUID, primary_key=True)
    phone_number = Column(String, nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
