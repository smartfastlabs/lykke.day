"""Domain events for the domain layer.

Domain events represent something important that happened in the domain.
They are raised by aggregate roots and dispatched after transaction commit.
"""

from .base import BaseAggregateRoot, DomainEvent

__all__ = [
    "BaseAggregateRoot",
    "DomainEvent",
]

