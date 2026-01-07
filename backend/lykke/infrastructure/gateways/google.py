import asyncio
import re
from datetime import UTC, date, datetime, timedelta

from gcsa.event import Event as GoogleEvent
from gcsa.google_calendar import GoogleCalendar
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from loguru import logger
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.core.config import settings
from lykke.core.exceptions import TokenExpiredError
from lykke.domain import data_objects, value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity

# Google OAuth Flow
CLIENT_SECRET_FILE = ".credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]
REDIRECT_URIS: dict[str, str] = {
    "login": "http://localhost:8080/google/callback/login",
    "calendar": "http://localhost:8080/google/callback/calendar",
}


def _parse_recurrence_frequency(
    recurrence: list[str] | None,
) -> value_objects.TaskFrequency:
    """Parse Google Calendar recurrence rules to determine TaskFrequency.

    Args:
        recurrence: List of RRULE strings from Google Calendar event.
                   Example: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"]

    Returns:
        The appropriate TaskFrequency enum value.
    """
    if not recurrence:
        return value_objects.TaskFrequency.ONCE

    for rule in recurrence:
        if not rule.startswith("RRULE:"):
            continue

        # Extract FREQ value
        freq_match = re.search(r"FREQ=(\w+)", rule)
        if not freq_match:
            continue

        freq = freq_match.group(1).upper()

        if freq == "DAILY":
            return value_objects.TaskFrequency.DAILY
        elif freq == "WEEKLY":
            # Check if it's a custom weekly schedule (multiple specific days)
            byday_match = re.search(r"BYDAY=([A-Z,]+)", rule)
            if byday_match:
                days = set(byday_match.group(1).split(","))
                print(days)
                # If more than one day specified, it's a custom weekly schedule
                if days == {"MO", "TU", "WE", "TH", "FR"}:
                    return value_objects.TaskFrequency.WEEK_DAYS
                elif days == {"SA", "SU"}:
                    return value_objects.TaskFrequency.WEEKEND_DAYS
                elif len(days) == 1:
                    return value_objects.TaskFrequency.WEEKLY
                elif len(days) == 2:
                    return value_objects.TaskFrequency.BI_WEEKLY
                return value_objects.TaskFrequency.CUSTOM_WEEKLY
        elif freq == "MONTHLY":
            return value_objects.TaskFrequency.MONTHLY
        elif freq == "YEARLY":
            return value_objects.TaskFrequency.YEARLY

    return value_objects.TaskFrequency.ONCE


def _get_event_frequency(
    event: GoogleEvent,
    gc: GoogleCalendar,
    frequency_cache: dict[str, value_objects.TaskFrequency],
) -> value_objects.TaskFrequency:
    """Determine the frequency of an event, fetching parent event if necessary.

    Args:
        event: The Google Calendar event (may be an instance of a recurring event).
        gc: The GoogleCalendar client for fetching parent events.
        frequency_cache: Cache of recurring_event_id -> TaskFrequency to avoid repeat lookups.

    Returns:
        The appropriate TaskFrequency enum value.
    """
    # Check if this event is an instance of a recurring event

    if not event.recurring_event_id:
        # Not a recurring event instance, check if it has its own recurrence
        recurrence = getattr(event, "recurrence", None)
        return _parse_recurrence_frequency(recurrence)

    # Check cache first
    if event.recurring_event_id in frequency_cache:
        return frequency_cache[event.recurring_event_id]

    # Fetch the parent event to get recurrence rules
    try:
        parent_event = gc.get_event(event.recurring_event_id)
        recurrence = getattr(parent_event, "recurrence", None)
        frequency = _parse_recurrence_frequency(recurrence)
    except Exception as e:
        logger.warning(
            f"Failed to fetch parent event {event.recurring_event_id} for event {event.id}: {e}"
        )
        frequency = value_objects.TaskFrequency.ONCE

    # Cache the result
    frequency_cache[event.recurring_event_id] = frequency
    return frequency


def _is_after(
    d1: datetime | date,
    d2: datetime | date,
) -> bool:
    if type(d1) is type(d2):
        return d2 > d1
    if isinstance(d1, datetime):
        d1 = d1.date()
    elif isinstance(d2, datetime):
        d2 = d2.date()
    return d2 > d1


class GoogleCalendarGateway(GoogleCalendarGatewayProtocol):
    """Gateway for interacting with Google Calendar API."""

    def _get_google_calendar(
        self, calendar: CalendarEntity, token: data_objects.AuthToken
    ) -> GoogleCalendar:
        """Create a GoogleCalendar client with the given credentials."""
        try:
            credentials = token.google_credentials()
            # Force a refresh check
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            return GoogleCalendar(
                calendar.platform_id,
                credentials=credentials,
                token_path=".token.pickle",
                credentials_path=CLIENT_SECRET_FILE,
                read_only=True,
            )
        except RefreshError as exc:
            raise TokenExpiredError("User needs to re-authenticate") from exc

    def _load_calendar_events_sync(
        self,
        calendar: CalendarEntity,
        token: data_objects.AuthToken,
    ) -> list[CalendarEntryEntity]:
        """Synchronous implementation of calendar entry loading."""
        calendar_entries: list[CalendarEntryEntity] = []
        frequency_cache: dict[str, value_objects.TaskFrequency] = {}

        logger.info(f"Loading calendar entries for calendar {calendar.name}...")
        gc = self._get_google_calendar(calendar, token)

        for event in gc.get_events(
            single_events=True,
            showDeleted=False,
            time_max=datetime.now(UTC) + timedelta(days=30),
        ):
            if _is_after(event.end, event.updated):
                logger.info(
                    f"It looks like the event `{event.summary}` has already happened"
                )
                continue
            if event.other.get("status") == "cancelled":
                logger.info(
                    f"It looks like the event `{event.summary}` has been cancelled"
                )
            try:
                # Get frequency, fetching parent event if this is a recurring instance
                frequency = _get_event_frequency(event, gc, frequency_cache)
                calendar_entries.append(
                    CalendarEntryEntity.from_google(
                        calendar.user_id,
                        calendar.id,
                        event,
                        frequency,
                        settings.TIMEZONE,
                    )
                )
            except Exception as e:
                logger.info(f"Error converting event {event.id}: {e}")
                continue
        return calendar_entries

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
        try:
            return await asyncio.to_thread(
                self._load_calendar_events_sync,
                calendar,
                token,
            )
        except RefreshError as exc:
            raise TokenExpiredError("User needs to re-authenticate") from exc

    def _subscribe_to_calendar_sync(
        self,
        calendar: CalendarEntity,
        token: data_objects.AuthToken,
        webhook_url: str,
        channel_id: str,
        client_state: str,
    ) -> value_objects.CalendarSubscription:
        """Synchronous implementation of calendar subscription."""
        try:
            credentials = token.google_credentials()
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            service = build("calendar", "v3", credentials=credentials)

            # Create the watch request body
            # The 'token' field is returned as X-Goog-Channel-Token in notifications
            watch_body = {
                "id": channel_id,
                "type": "web_hook",
                "address": webhook_url,
                "token": client_state,
            }

            # Execute the watch request
            # pylint: disable=no-member  # Dynamic API client
            response = (
                service.events()
                .watch(
                    calendarId=calendar.platform_id,
                    body=watch_body,
                )
                .execute()
            )

            # Parse expiration timestamp (milliseconds since epoch)
            expiration_ms = int(response["expiration"])
            expiration = datetime.fromtimestamp(expiration_ms / 1000, tz=UTC)

            return value_objects.CalendarSubscription(
                channel_id=response["id"],
                resource_id=response["resourceId"],
                expiration=expiration,
            )
        except RefreshError as exc:
            raise TokenExpiredError("User needs to re-authenticate") from exc

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
        return await asyncio.to_thread(
            self._subscribe_to_calendar_sync,
            calendar,
            token,
            webhook_url,
            channel_id,
            client_state,
        )

    @staticmethod
    def get_flow(flow_name: str) -> Flow:
        """Get OAuth flow for Google authentication.

        Args:
            flow_name: The name of the flow (e.g., 'login', 'calendar').

        Returns:
            The OAuth flow object.
        """
        return Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URIS[flow_name],
        )
