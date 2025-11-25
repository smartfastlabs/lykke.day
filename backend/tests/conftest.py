import pytest
import datetime
from freezegun import freeze_time

from planned import objects
from planned.utils.dates import get_current_date

@pytest.fixture
def today():
    return get_current_date()

@pytest.fixture
def test_date():
    with freeze_time("2025-11-27"):
        yield datetime.date(2025, 11, 27)