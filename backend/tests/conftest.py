import datetime

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from planned import objects
from planned.app import app
from planned.utils.dates import get_current_date


@pytest.fixture
def today():
    return get_current_date()


@pytest.fixture
def test_date():
    with freeze_time("2025-11-27 00:00:00-6:00"):
        yield datetime.date(2025, 11, 27)


client = TestClient(app)


@pytest.fixture
def test_client():
    return client
