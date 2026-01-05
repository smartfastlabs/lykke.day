"""Domain events for the domain layer.

Domain events represent something important that happened in the domain.
They are raised by entities (aggregate roots) and dispatched after transaction commit.
"""

from .base import DomainEvent, EntityUpdatedEvent

__all__ = [
    "DomainEvent",
    "EntityUpdatedEvent",
]

