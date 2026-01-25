"""Audit logs table definition."""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class AuditLog(Base):
    """Audit log table for storing user activity entries."""

    __tablename__ = "audit_logs"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    date = Column(Date, nullable=False)
    entity_id = Column(PGUUID, nullable=True)
    entity_type = Column(String, nullable=True)
    meta = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_activity_type", "activity_type"),
        Index("idx_audit_logs_occurred_at", "occurred_at"),
        Index("idx_audit_logs_entity_id", "entity_id"),
        Index("idx_audit_logs_user_occurred", "user_id", "occurred_at"),
        Index("idx_audit_logs_user_activity", "user_id", "activity_type"),
        Index("idx_audit_logs_user_date", "user_id", "date"),
    )
