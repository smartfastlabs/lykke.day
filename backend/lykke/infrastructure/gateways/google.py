import asyncio
import json
import re
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.core.config import settings
from lykke.core.exceptions import TokenExpiredError
from lykke.domain import value_objects
from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
)

# Google OAuth Flow
CLIENT_SECRET_FILE = ".credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def _build_redirect_uri(path: str) -> str:
    """Build redirect URI using configured web domain."""
    base_domain = settings.WEB_DOMAIN.rstrip("/")
    return f"{base_domain}{path}"


REDIRECT_URIS: dict[str, str] = {
    "login": _build_redirect_uri("/api/google/callback/login"),
    "calendar": _build_redirect_uri("/api/google/callback/calendar"),
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


class GoogleCalendarGateway(GoogleCalendarGatewayProtocol):
    """Gateway for interacting with Google Calendar API."""

    @staticmethod
    @lru_cache(maxsize=256)
    def _log_invalid_event_timestamp(value: str) -> None:
        logger.warning(
            "Invalid Google event timestamp received: {value}",
            value=value,
        )

    @staticmethod
    def _parse_event_timestamp(value: Any) -> datetime:
        """Parse a Google event timestamp into a safe UTC datetime."""
        if not isinstance(value, str):
            return datetime.now(UTC)

        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except (TypeError, ValueError):
            GoogleCalendarGateway._log_invalid_event_timestamp(value)
            return datetime.now(UTC)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)

    @staticmethod
    def _derive_recurring_event_id(event_id: str) -> str | None:
        """Derive recurring event id from instance ids when missing."""
        match = re.search(r"_\d{8}T\d{6}Z?$", event_id)
        if not match:
            return None
        return event_id[: match.start()]

    @staticmethod
    def _client_config_from_env() -> dict[str, Any] | None:
        """Return OAuth client config from env if provided."""
        credentials_json = settings.GOOGLE_CREDENTIALS_JSON.strip()
        if not credentials_json:
            return None

        try:
            return cast("dict[str, Any]", json.loads(credentials_json))
        except json.JSONDecodeError as exc:
            logger.error("GOOGLE_CREDENTIALS_JSON is not valid JSON")
            raise ValueError("Invalid GOOGLE_CREDENTIALS_JSON") from exc

    @staticmethod
    def _parse_datetime(
        value: dict[str, Any] | None,
        fallback_timezone: str,
        use_start_of_day: bool,
    ) -> datetime:
        """Parse Google Calendar date/datetime dicts into aware datetimes."""
        if not value:
            # Fallback to now to satisfy required fields; caller should override if needed
            return datetime.now(UTC)

        if date_time := value.get("dateTime"):
            # dateTime already includes timezone info
            # Replace trailing Z for fromisoformat compatibility
            normalized = date_time.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(normalized)
            except ValueError:
                dt = datetime.now(UTC)
            return dt.astimezone(UTC)

        if date_only := value.get("date"):
            try:
                parsed_date = datetime.fromisoformat(date_only).date()
            except ValueError:
                parsed_date = datetime.now(UTC).date()
            return datetime.combine(
                parsed_date,
                datetime.min.time() if use_start_of_day else datetime.max.time(),
                tzinfo=ZoneInfo(fallback_timezone),
            ).astimezone(UTC)

        return datetime.now(UTC)

    def _google_event_to_entity(
        self,
        calendar: CalendarEntity,
        event: dict[str, Any],
        frequency_cache: dict[str, value_objects.TaskFrequency],
        recurrence_lookup: Any,
        user_timezone: str | None = None,
    ) -> tuple[CalendarEntryEntity, CalendarEntrySeriesEntity | None]:
        """Convert a Google API event dict to CalendarEntryEntity and optional series."""
        status = event.get("status", "confirmed")
        recurrence = event.get("recurrence")
        recurring_event_id = event.get("recurringEventId")
        if not recurring_event_id and isinstance(event.get("id"), str):
            recurring_event_id = self._derive_recurring_event_id(event["id"])
        has_recurrence = (
            bool(recurrence)
            or bool(recurring_event_id)
            or bool(event.get("originalStartTime"))
        )
        series_platform_id = recurring_event_id or (
            event.get("id") if recurrence else None
        )
        if not series_platform_id and has_recurrence:
            ical_uid = event.get("iCalUID")
            if isinstance(ical_uid, str) and ical_uid:
                series_platform_id = ical_uid
        frequency = self._determine_frequency(
            calendar_id=calendar.platform_id,
            recurrence=recurrence,
            recurring_event_id=recurring_event_id,
            recurrence_lookup=recurrence_lookup,
            frequency_cache=frequency_cache,
        )
        series_id = (
            CalendarEntrySeriesEntity.id_from_platform("google", series_platform_id)
            if series_platform_id
            else None
        )

        fallback_timezone = event.get("timeZone") or user_timezone or "UTC"
        start_dt = self._parse_datetime(
            event.get("start"),
            fallback_timezone=fallback_timezone,
            use_start_of_day=True,
        )
        end_dt = self._parse_datetime(
            event.get("end"),
            fallback_timezone=fallback_timezone,
            use_start_of_day=False,
        )

        created = event.get("created")
        updated = event.get("updated")
        created_dt = self._parse_event_timestamp(created)
        updated_dt = self._parse_event_timestamp(updated)

        summary = event.get("summary")
        if isinstance(summary, str):
            summary = summary.strip()
        if not summary:
            summary = "(no title)"

        series_entity = None
        if series_id and series_platform_id:
            series_entity = CalendarEntrySeriesEntity(
                id=series_id,
                user_id=calendar.user_id,
                calendar_id=calendar.id,
                name=summary,
                platform_id=series_platform_id,
                platform="google",
                frequency=frequency,
                event_category=calendar.default_event_category,
                recurrence=recurrence or [],
                starts_at=start_dt,
                ends_at=end_dt,
                created_at=created_dt,
                updated_at=updated_dt,
            )

        entry_category = (
            series_entity.event_category
            if series_entity and series_entity.event_category
            else calendar.default_event_category
        )
        is_instance_exception = self._is_instance_exception(event, series_id)
        entry = CalendarEntryEntity(
            user_id=calendar.user_id,
            calendar_id=calendar.id,
            calendar_entry_series_id=series_id,
            platform_id=event.get("id", "NA"),
            platform="google",
            status=status,
            name=summary,
            starts_at=start_dt,
            ends_at=end_dt,
            frequency=frequency,
            created_at=created_dt,
            updated_at=updated_dt,
            timezone=event.get("start", {}).get("timeZone") or user_timezone,
            user_timezone=user_timezone,
            category=entry_category,
            is_instance_exception=is_instance_exception,
        )

        return entry, series_entity

    @staticmethod
    def _is_instance_exception(event: dict[str, Any], series_id: UUID | None) -> bool:
        """Classify whether this Google event is a single-instance exception.

        Instance exceptions are recurring occurrences that were explicitly modified
        (e.g. moved or retitled). Google sets originalStartTime when the instance
        was changed from the default.

        Returns:
            True if the event represents an instance-level exception; False otherwise.
        """
        if series_id is None:
            return False
        return bool(event.get("originalStartTime"))

    def _determine_frequency(
        self,
        calendar_id: str,
        recurrence: list[str] | None,
        recurring_event_id: str | None,
        recurrence_lookup: Any,
        frequency_cache: dict[str, value_objects.TaskFrequency],
    ) -> value_objects.TaskFrequency:
        """Determine recurrence frequency using cache and parent lookups."""
        if recurrence:
            return _parse_recurrence_frequency(recurrence)

        if not recurring_event_id:
            return value_objects.TaskFrequency.ONCE

        if recurring_event_id in frequency_cache:
            return frequency_cache[recurring_event_id]

        try:
            parent_event = (
                recurrence_lookup.events()
                .get(calendarId=calendar_id, eventId=recurring_event_id)
                .execute()
            )
            parent_recurrence = parent_event.get("recurrence")
            frequency = _parse_recurrence_frequency(parent_recurrence)
        except Exception as exc:
            logger.warning(f"Failed to fetch parent event {recurring_event_id}: {exc}")
            frequency = value_objects.TaskFrequency.ONCE

        frequency_cache[recurring_event_id] = frequency
        return frequency

    def _load_cancelled_series_ids_sync(
        self,
        service: Any,
        calendar: CalendarEntity,
        lookback: datetime,
        sync_token: str | None,
    ) -> set[UUID]:
        cancelled_series_ids: set[UUID] = set()
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "calendarId": calendar.platform_id,
                "showDeleted": True,
                "singleEvents": False,
                "maxResults": 2500,
            }
            if sync_token:
                params["syncToken"] = sync_token
            else:
                params["timeMin"] = lookback.astimezone(UTC).isoformat()

            if page_token:
                params["pageToken"] = page_token

            response = service.events().list(**params).execute()

            for event in response.get("items", []):
                if event.get("status") != "cancelled":
                    continue
                event_id = event.get("id")
                if not isinstance(event_id, str):
                    continue
                cancelled_series_ids.add(
                    CalendarEntrySeriesEntity.id_from_platform("google", event_id)
                )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return cancelled_series_ids

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
        list[UUID],
        str | None,
    ]:
        """Load calendar entries and series from Google Calendar (full or incremental).

        Args:
            calendar: The calendar to load entries from.
            lookback: The datetime to look back from.
            token: The authentication token.

        Returns:
            Tuple of (new/updated entries, deleted entries, series, next sync token).
        """
        try:
            return await asyncio.to_thread(
                self._load_calendar_events_sync,
                calendar,
                lookback,
                token,
                user_timezone,
                sync_token,
            )
        except RefreshError as exc:
            raise TokenExpiredError("User needs to re-authenticate") from exc

    def _load_calendar_events_sync(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        token: AuthTokenEntity,
        user_timezone: str | None,
        sync_token: str | None,
    ) -> tuple[
        list[CalendarEntryEntity],
        list[CalendarEntryEntity],
        list[CalendarEntrySeriesEntity],
        list[UUID],
        str | None,
    ]:
        """Fetch events using Google API with support for sync tokens."""
        credentials = token.google_credentials()
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        service = build("calendar", "v3", credentials=credentials)
        events: list[CalendarEntryEntity] = []
        deleted: list[CalendarEntryEntity] = []
        series_entities: dict[UUID, CalendarEntrySeriesEntity] = {}
        frequency_cache: dict[str, value_objects.TaskFrequency] = {}
        next_sync_token: str | None = None
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "calendarId": calendar.platform_id,
                "showDeleted": True,
                "singleEvents": True,
                "maxResults": 2500,
            }
            if sync_token:
                params["syncToken"] = sync_token
            else:
                params["timeMin"] = lookback.astimezone(UTC).isoformat()

            if page_token:
                params["pageToken"] = page_token

            response = service.events().list(**params).execute()
            recurrence_lookup = service

            for event in response.get("items", []):
                entry, series_entity = self._google_event_to_entity(
                    calendar=calendar,
                    event=event,
                    frequency_cache=frequency_cache,
                    recurrence_lookup=recurrence_lookup,
                    user_timezone=user_timezone,
                )
                if series_entity:
                    existing_series = series_entities.get(series_entity.id)
                    if (
                        existing_series is None
                        or series_entity.updated_at > existing_series.updated_at
                    ):
                        series_entities[series_entity.id] = series_entity
                if entry.status == "cancelled":
                    deleted.append(entry)
                else:
                    events.append(entry)

            next_sync_token = response.get("nextSyncToken", next_sync_token)
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        cancelled_series_ids = self._load_cancelled_series_ids_sync(
            service=service,
            calendar=calendar,
            lookback=lookback,
            sync_token=sync_token,
        )

        return (
            events,
            deleted,
            list(series_entities.values()),
            list(cancelled_series_ids),
            next_sync_token,
        )

    def _subscribe_to_calendar_sync(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
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
        return await asyncio.to_thread(
            self._subscribe_to_calendar_sync,
            calendar,
            token,
            webhook_url,
            channel_id,
            client_state,
        )

    def _unsubscribe_from_calendar_sync(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        channel_id: str,
        resource_id: str | None,
    ) -> None:
        """Synchronous implementation to stop a calendar watch channel."""
        try:
            credentials = token.google_credentials()
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            service = build("calendar", "v3", credentials=credentials)

            stop_body = {"id": channel_id}
            if resource_id:
                stop_body["resourceId"] = resource_id

            # pylint: disable=no-member  # Dynamic API client
            service.channels().stop(body=stop_body).execute()
        except HttpError as exc:
            if exc.resp.status == 404:
                logger.info(
                    "Calendar channel already stopped or expired",
                    channel_id=channel_id,
                    resource_id=resource_id,
                )
                return
            raise
        except RefreshError as exc:
            raise TokenExpiredError("User needs to re-authenticate") from exc

    async def unsubscribe_from_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        channel_id: str,
        resource_id: str | None,
    ) -> None:
        """Unsubscribe from push notifications for calendar updates."""
        await asyncio.to_thread(
            self._unsubscribe_from_calendar_sync,
            calendar,
            token,
            channel_id,
            resource_id,
        )

    @staticmethod
    def get_flow(flow_name: str) -> Flow:
        """Get OAuth flow for Google authentication.

        Args:
            flow_name: The name of the flow (e.g., 'login', 'calendar').

        Returns:
            The OAuth flow object.
        """
        if client_config := GoogleCalendarGateway._client_config_from_env():
            return Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URIS[flow_name],
            )

        return Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URIS[flow_name],
        )
