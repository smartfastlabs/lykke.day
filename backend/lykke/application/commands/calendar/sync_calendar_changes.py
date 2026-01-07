"""Backward-compatible wrapper for calendar sync handler."""

from lykke.application.commands.calendar.sync_calendar import SyncCalendarHandler
from lykke.domain.entities import CalendarEntity


class SyncCalendarChangesHandler(SyncCalendarHandler):
    """Backward-compatible wrapper; prefer SyncCalendarHandler directly."""

    async def sync(self, calendar: CalendarEntity) -> CalendarEntity:
        """Delegate to the unified sync handler."""
        return await self.sync_calendar_entity(calendar)
