"""E2E tests for the /me endpoints."""

import pytest

from lykke.core.utils.dates import get_current_date
from lykke.domain import value_objects
from lykke.domain.entities.day import DayEntity
from lykke.infrastructure.repositories import (
    DayRepository,
    DayTemplateRepository,
    UserRepository,
)


@pytest.mark.asyncio
async def test_get_current_user_profile(authenticated_client):
    client, user = await authenticated_client()

    response = client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["settings"]["template_defaults"] == user.settings.template_defaults


@pytest.mark.asyncio
async def test_update_current_user_profile(authenticated_client):
    client, user = await authenticated_client()

    # Generate a unique, valid-ish NANP number per user to avoid unique constraint collisions
    unique_suffix = int(user.id.hex[-7:], 16) % 10_000_000
    suffix = f"{unique_suffix:07d}"
    exchange_first = str((int(suffix[0]) % 8) + 2)  # 2-9
    national = f"202{exchange_first}{suffix[1:3]}{suffix[3:]}"  # 10 digits
    phone_number = national  # user-entered form (no +1)
    expected_e164 = f"+1{national}"
    payload = {
        "phone_number": phone_number,
        "status": "new-lead",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "settings": {
            "template_defaults": ["m", "t", "w", "th", "f", "sa", "su"],
        },
    }

    response = client.put("/me", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == expected_e164
    assert data["status"] == "new-lead"
    assert data["is_verified"] is True
    assert data["settings"]["template_defaults"] == [
        "m",
        "t",
        "w",
        "th",
        "f",
        "sa",
        "su",
    ]
    # email should remain unchanged
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_update_current_user_profile_requires_seven_defaults(
    authenticated_client,
):
    client, _ = await authenticated_client()

    payload = {
        "settings": {"template_defaults": ["only-one"]},
    }

    response = client.put("/me", json=payload)

    # Pydantic validation should fail with 422 Unprocessable Entity
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_current_user_persists_settings_and_updates_timestamp(
    authenticated_client,
):
    """Ensure settings changes persist to DB and updated_at is refreshed."""
    client, user = await authenticated_client()
    original_updated_at = user.updated_at

    unique_suffix = int(user.id.hex[-7:], 16) % 10_000_000
    suffix = f"{unique_suffix:07d}"
    exchange_first = str((int(suffix[0]) % 8) + 2)  # 2-9
    national = f"303{exchange_first}{suffix[1:3]}{suffix[3:]}"  # 10 digits, different area code
    phone_number = national
    expected_e164 = f"+1{national}"
    payload = {
        "phone_number": phone_number,
        "settings": {
            "template_defaults": ["x", "x", "x", "x", "x", "x", "x"],
        },
    }

    response = client.put("/me", json=payload)
    assert response.status_code == 200

    # Fetch fresh from repository to ensure persistence
    repo = UserRepository()
    updated_user = await repo.get(user.id)

    assert updated_user.settings.template_defaults == ["x"] * 7
    assert updated_user.phone_number == expected_e164
    assert updated_user.updated_at is not None
    assert updated_user.updated_at != original_updated_at


@pytest.mark.asyncio
async def test_update_today_high_level_plan_persists(authenticated_client):
    client, user = await authenticated_client()

    # Create today's day so reschedule can run
    today = get_current_date()
    template_slug = user.settings.template_defaults[today.weekday()]
    template_repo = DayTemplateRepository(user=user)
    template = await template_repo.search_one(
        value_objects.DayTemplateQuery(slug=template_slug)
    )
    day_repo = DayRepository(user=user)
    await day_repo.put(
        DayEntity.create_for_date(today, user_id=user.id, template=template)
    )

    # Ensure today's day exists
    reschedule_response = client.put("/days/today/reschedule")
    assert reschedule_response.status_code == 200
    reschedule_data = reschedule_response.json()
    day_id = reschedule_data["day"]["id"]

    payload = {
        "title": "Focus",
        "text": "Ship the high level plan",
        "intentions": ["Be present", "Stay focused"],
    }
    response = client.patch(
        f"/days/{day_id}",
        json={"high_level_plan": payload},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["high_level_plan"]["title"] == payload["title"]
    assert data["high_level_plan"]["text"] == payload["text"]
    assert data["high_level_plan"]["intentions"] == payload["intentions"]
    assert data["status"] == "STARTED"
    repo = DayRepository(user=user)
    updated_day = await repo.get(day_id)

    assert updated_day.high_level_plan is not None
    assert updated_day.high_level_plan.title == payload["title"]
    assert updated_day.high_level_plan.text == payload["text"]
    assert updated_day.high_level_plan.intentions == payload["intentions"]
    assert updated_day.status.value == "STARTED"
