"""Marker interface for entities that should generate audit logs."""


class AuditableEntity:
    """Marker interface for entities that should generate audit logs.

    Entities that inherit from this will have their EntityCreatedEvent,
    EntityUpdatedEvent, and EntityDeletedEvent automatically converted
    to audit logs.
    """

    pass
