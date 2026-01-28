"""Global pytest configuration and fixtures shared across all tests."""

import datetime
import os
from datetime import UTC

import pytest
from freezegun import freeze_time

from lykke.core.config import settings
from lykke.core.utils.dates import get_current_date


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL - should be PostgreSQL for tests."""
    # Use DATABASE_URL from environment if set, otherwise use settings
    # This allows the Makefile to set the test database URL
    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("TEST_DATABASE_URL")
        or settings.DATABASE_URL
    )
    return database_url


@pytest.fixture
def today():
    """Get current date."""
    return get_current_date()


@pytest.fixture
def test_date():
    """Fixed test date for consistent testing."""
    with freeze_time(
        "2025-11-27 00:00:00-6:00",
        real_asyncio=True,
    ):
        yield datetime.date(2025, 11, 27)


@pytest.fixture
def test_date_tomorrow(test_date):
    """Test date for tomorrow."""
    return test_date + datetime.timedelta(days=1)


@pytest.fixture
def test_date_yesterday(test_date):
    """Test date for yesterday."""
    return test_date - datetime.timedelta(days=1)


@pytest.fixture
def test_datetime_noon():
    """Fixed test datetime at noon UTC for consistent testing."""
    with freeze_time(
        "2025-11-27 12:00:00-6:00",
        real_asyncio=True,
    ):
        yield datetime.datetime(2025, 11, 27, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def test_datetime_morning():
    """Fixed test datetime in the morning UTC for consistent testing."""
    with freeze_time(
        "2025-11-27 08:00:00-6:00",
        real_asyncio=True,
    ):
        yield datetime.datetime(2025, 11, 27, 8, 0, 0, tzinfo=UTC)


@pytest.fixture
def test_datetime_evening():
    """Fixed test datetime in the evening UTC for consistent testing."""
    with freeze_time(
        "2025-11-27 18:00:00-6:00",
        real_asyncio=True,
    ):
        yield datetime.datetime(2025, 11, 27, 18, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def vcr_config():
    """Default VCR configuration for recorded HTTP interactions."""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
    }
