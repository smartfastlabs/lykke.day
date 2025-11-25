from datetime import UTC, date, datetime, timedelta

from gcsa.google_calendar import GoogleCalendar
from google_auth_oauthlib.flow import Flow

from planned.objects import Calendar, Event
from planned.objects.auth_token import AuthToken

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


def get_flow(flow_name: str):
    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URIS[flow_name],
    )


def get_google_calendar(calendar: Calendar, token: AuthToken) -> GoogleCalendar:
    return GoogleCalendar(
        calendar.platform_id,
        credentials=token.google_credentials(),
        token_path=".token.pickle",
        credentials_path=CLIENT_SECRET_FILE,
        read_only=True,
    )


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


def load_calendar_events(
    calendar: Calendar,
    lookback: datetime,
    token: AuthToken,
) -> list[Event]:
    events: list[Event] = []
    print(f"Loading events for calendar {calendar.name}...")
    for e in get_google_calendar(calendar, token).get_events(
        single_events=True,
        showDeleted=False,
        time_max=datetime.now(UTC) + timedelta(days=30),
    ):
        if is_after(e.end, e.updated):
            print(f"It looks like the event `{e.summary}` has already happened")
            continue

        if e.other.get("status") == "cancelled":
            print(f"It looks like the event `{e.summary}` has been cancelled")

        else:
            print(f"Loaded event {e.id}: {e.summary}")

        try:
            events.append(Event.from_google(calendar.id, e))
        except Exception as e:
            print(f"Error converting event {e.id}: {e}")
            continue

    return events
