"""Protocol for Google Calendar gateway."""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from lykke.domain import data_objects, value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity

if TYPE_CHECKING:
    from google_auth_oauthlib.flow import Flow


class GoogleCalendarGatewayProtocol(Protocol):
    """Protocol defining the interface for Google Calendar gateways."""

    async def load_calendar_events(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        token: data_objects.AuthToken,
    ) -> list[CalendarEntryEntity]:
        """Load calendar entries from Google Calendar.

        Args:
            calendar: The calendar to load entries from.
            lookback: The datetime to look back from.
            token: The authentication token.

        Returns:
            List of calendar entries from the calendar.
        """
        ...

    async def subscribe_to_calendar(
        self,
        calendar: CalendarEntity,
        token: data_objects.AuthToken,
        webhook_url: str,
        channel_id: str,
        client_state: str,
    ) -> value_objects.CalendarSubscription:
        """Subscribe to push notifications for calendar updates.

        Creates a watch channel on the specified calendar that will send
        push notifications to the webhook URL when events change.

        Args:
            calendar: The calendar to subscribe to.
            token: The authentication token.
            webhook_url: The HTTPS URL to receive push notifications.
            channel_id: Unique identifier for the notification channel.
            client_state: Secret token for webhook verification.

        Returns:
            CalendarSubscription with channel details and expiration.
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
