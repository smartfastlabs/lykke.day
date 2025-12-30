"""Auth tokens table definition."""

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class AuthToken(Base):
    """Auth token table for storing OAuth tokens."""

    __tablename__ = "auth_tokens"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    platform = Column(String, nullable=False)
    token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_uri = Column(Text)
    client_id = Column(Text)
    client_secret = Column(Text)
    scopes = Column(JSONB)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("idx_auth_tokens_user_id", "user_id"),)

