"""Unit tests for Google Calendar gateway helpers."""

# pylint: disable=protected-access

from datetime import UTC, datetime

from freezegun import freeze_time

from lykke.infrastructure.gateways.google import GoogleCalendarGateway


def test_parse_event_timestamp_valid_z() -> None:
    """Parses ISO timestamps with Z suffix into UTC."""
    result = GoogleCalendarGateway._parse_event_timestamp(
        "2026-02-02T08:15:37.614Z"
    )

    assert result == datetime(2026, 2, 2, 8, 15, 37, 614000, tzinfo=UTC)


def test_parse_event_timestamp_naive_assumes_utc() -> None:
    """Naive timestamps are treated as UTC."""
    result = GoogleCalendarGateway._parse_event_timestamp(
        "2026-02-02T08:15:37.614"
    )

    assert result == datetime(2026, 2, 2, 8, 15, 37, 614000, tzinfo=UTC)


def test_parse_event_timestamp_invalid_year_falls_back() -> None:
    """Invalid years fall back to the current UTC time."""
    with freeze_time("2026-02-02 09:00:00+00:00", real_asyncio=True):
        result = GoogleCalendarGateway._parse_event_timestamp(
            "0000-12-31T00:00:00.000Z"
        )

    assert result == datetime(2026, 2, 2, 9, 0, 0, tzinfo=UTC)


def test_parse_event_timestamp_non_string_falls_back() -> None:
    """Non-string values fall back to the current UTC time."""
    with freeze_time("2026-02-02 09:30:00+00:00", real_asyncio=True):
        result = GoogleCalendarGateway._parse_event_timestamp(None)

    assert result == datetime(2026, 2, 2, 9, 30, 0, tzinfo=UTC)
