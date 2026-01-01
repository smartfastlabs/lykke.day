import asyncio
import re
from datetime import UTC, date, datetime, timedelta

from gcsa.event import Event as GoogleEvent
from gcsa.google_calendar import GoogleCalendar
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from loguru import logger

from planned.core.config import settings
from planned.core.exceptions import TokenExpiredError
from planned.domain.entities import AuthToken, Calendar, Event, TaskFrequency

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


def get_flow(flow_name: str) -> Flow:
    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URIS[flow_name],
    )


def get_google_calendar(calendar: Calendar, token: AuthToken) -> GoogleCalendar:
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
    except RefreshError:
        # Token is invalid - need to re-authenticate
        raise TokenExpiredError("User needs to re-authenticate")


def parse_recurrence_frequency(recurrence: list[str] | None) -> TaskFrequency:
    """Parse Google Calendar recurrence rules to determine TaskFrequency.

    Args:
        recurrence: List of RRULE strings from Google Calendar event.
                   Example: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"]

    Returns:
        The appropriate TaskFrequency enum value.
    """
    if not recurrence:
        return TaskFrequency.ONCE

    for rule in recurrence:
        if not rule.startswith("RRULE:"):
            continue

        # Extract FREQ value
        freq_match = re.search(r"FREQ=(\w+)", rule)
        if not freq_match:
            continue

        freq = freq_match.group(1).upper()

        if freq == "DAILY":
            return TaskFrequency.DAILY
        elif freq == "WEEKLY":
            # Check if it's a custom weekly schedule (multiple specific days)
            byday_match = re.search(r"BYDAY=([A-Z,]+)", rule)
            if byday_match:
                days = set(byday_match.group(1).split(","))
                print(days)
                # If more than one day specified, it's a custom weekly schedule
                if days == {"MO", "TU", "WE", "TH", "FR"}:
                    return TaskFrequency.WEEK_DAYS
                elif days == {"SA", "SU"}:
                    return TaskFrequency.WEEKEND_DAYS
                elif len(days) == 1:
                    return TaskFrequency.WEEKLY
                elif len(days) == 2:
                    return TaskFrequency.BI_WEEKLY
                return TaskFrequency.CUSTOM_WEEKLY
        elif freq == "MONTHLY":
            return TaskFrequency.MONTHLY
        elif freq == "YEARLY":
            return TaskFrequency.YEARLY

    return TaskFrequency.ONCE


def get_event_frequency(
    event: GoogleEvent,
    gc: GoogleCalendar,
    frequency_cache: dict[str, TaskFrequency],
) -> TaskFrequency:
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
        return parse_recurrence_frequency(recurrence)

    # Check cache first
    if event.recurring_event_id in frequency_cache:
        return frequency_cache[event.recurring_event_id]

    # Fetch the parent event to get recurrence rules
    try:
        parent_event = gc.get_event(event.recurring_event_id)
        recurrence = getattr(parent_event, "recurrence", None)
        frequency = parse_recurrence_frequency(recurrence)
    except Exception as e:
        logger.warning(
            f"Failed to fetch parent event {event.recurring_event_id} for event {event.id}: {e}"
        )
        frequency = TaskFrequency.ONCE

    # Cache the result
    frequency_cache[event.recurring_event_id] = frequency
    return frequency


def is_after(
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


def _load_calendar_events_sync(
    calendar: Calendar,
    lookback: datetime,
    token: AuthToken,
) -> list[Event]:
    """Synchronous implementation of calendar event loading."""
    events: list[Event] = []
    frequency_cache: dict[str, TaskFrequency] = {}

    logger.info(f"Loading events for calendar {calendar.name}...")
    gc = get_google_calendar(calendar, token)

    for event in gc.get_events(
        single_events=True,
        showDeleted=False,
        time_max=datetime.now(UTC) + timedelta(days=30),
    ):
        if is_after(event.end, event.updated):
            logger.info(
                f"It looks like the event `{event.summary}` has already happened"
            )
            continue
        if event.other.get("status") == "cancelled":
            logger.info(f"It looks like the event `{event.summary}` has been cancelled")
        try:
            # Get frequency, fetching parent event if this is a recurring instance
            frequency = get_event_frequency(event, gc, frequency_cache)
            events.append(
                Event.from_google(
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
    return events


async def load_calendar_events(
    calendar: Calendar,
    lookback: datetime,
    token: AuthToken,
) -> list[Event]:
    """Asynchronously load calendar events by running the sync operation in a thread pool."""
    try:
        return await asyncio.to_thread(
            _load_calendar_events_sync,
            calendar,
            lookback,
            token,
        )
    except RefreshError:
        raise TokenExpiredError("User needs to re-authenticate")
