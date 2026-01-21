"""Auditable schema."""

from .base import BaseSchema


class AuditableSchema(BaseSchema):
    """Schema for Auditable marker interface.
    
    Note: AuditableEntity is a marker interface with no fields.
    This schema exists to satisfy the mapper completeness checker.
    """

    pass
