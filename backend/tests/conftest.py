"""Global pytest configuration and fixtures shared across all tests."""

import datetime
import os

import pytest
from freezegun import freeze_time

from planned.core.config import settings
from planned.infrastructure.utils.dates import get_current_date


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
