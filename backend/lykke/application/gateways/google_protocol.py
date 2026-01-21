"""Protocol for Google Calendar gateway."""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity
from lykke.domain.entities import (
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
)

if TYPE_CHECKING:
    from google_auth_oauthlib.flow import Flow


class GoogleCalendarGatewayProtocol(Protocol):
    """Protocol defining the interface for Google Calendar gateways."""

    async def load_calendar_events(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        token: AuthTokenEntity,
        *,
        user_timezone: str | None = None,
        sync_token: str | None = None,
    ) -> tuple[
        list[CalendarEntryEntity],
        list[CalendarEntryEntity],
        list[CalendarEntrySeriesEntity],
        str | None,
    ]:
        """Load calendar entries and series from Google Calendar (full or incremental).

        Args:
            calendar: The calendar to load entries from.
            lookback: The datetime to look back from.
            token: The authentication token.
            sync_token: Optional sync token for incremental syncs. If provided,
                only changes since the token will be returned.

        Returns:
            Tuple of (new/updated entries, deleted entries, series, next sync token).
        """
        ...

    async def subscribe_to_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
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

    async def unsubscribe_from_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        channel_id: str,
        resource_id: str | None,
    ) -> None:
        """Unsubscribe from push notifications for calendar updates.

        Args:
            calendar: The calendar to unsubscribe from.
            token: The authentication token.
            channel_id: The channel identifier previously returned by subscribe.
            resource_id: The resource identifier returned by subscribe (if provided).
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
