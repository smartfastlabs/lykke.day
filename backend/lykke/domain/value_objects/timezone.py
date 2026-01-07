"""Timezone provider protocol for domain layer."""

from typing import Protocol


class TimeZoneProvider(Protocol):
    """Protocol for providing timezone information to domain entities."""

    @property
    def timezone(self) -> str:
        """Return the timezone string (e.g., 'America/Chicago')."""
        ...

