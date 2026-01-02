"""Protocol for Google Calendar gateway."""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from planned.domain import entities

if TYPE_CHECKING:
    from google_auth_oauthlib.flow import Flow


class GoogleCalendarGatewayProtocol(Protocol):
    """Protocol defining the interface for Google Calendar gateways."""

    async def load_calendar_events(
        self,
        calendar: entities.Calendar,
        lookback: datetime,
        token: entities.AuthToken,
    ) -> list[entities.CalendarEntry]:
        """Load calendar entries from Google Calendar.

        Args:
            calendar: The calendar to load entries from.
            lookback: The datetime to look back from.
            token: The authentication token.

        Returns:
            List of calendar entries from the calendar.
        """
        ...

    def get_flow(self, flow_name: str) -> "Flow":
        """Get OAuth flow for Google authentication.

        Args:
            flow_name: The name of the flow (e.g., 'login', 'calendar').

        Returns:
            The OAuth flow object.
        """
        ...

