"""True E2E integration test - full user flow without mocks.

This test:
1. Registers a new user via API
2. Logs in as that user via API (using real session)
3. Loads data via API
4. Verifies database state directly
"""

from datetime import time
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from planned.domain.entities import Alarm, DayTemplate
from planned.domain.value_objects.alarm import AlarmType
from planned.domain.value_objects.day import DayStatus
from planned.infrastructure.database.utils import reset_engine
from planned.infrastructure.repositories import (
    DayRepository,
    DayTemplateRepository,
    UserRepository,
)


@pytest.mark.asyncio
async def test_full_user_flow_e2e(test_client: TestClient):
    """Complete E2E test: register -> login -> load data -> verify DB state."""
    # Reset database engine to ensure clean state
    await reset_engine()

    # Step 1: Register a new user
    email = f"test-{uuid4()}@example.com"
    password = "test_password_123"

    register_response = test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201, (
        f"Registration failed: {register_response.text}"
    )
    register_data = register_response.json()
    assert register_data["email"] == email
    user_id_str = register_data["id"]
    assert user_id_str is not None

    # Verify user exists in database after registration
    user_repo = UserRepository()
    user_from_db = await user_repo.get_by_email(email)
    assert user_from_db is not None, "User should exist in database after registration"
    assert user_from_db.email == email
    assert user_from_db.hashed_password is not None, "Password hash should be set"
    assert str(user_from_db.id) == user_id_str

    # Step 2: Login as the user (using fastapi-users login endpoint)
    # fastapi-users uses form data for login, not JSON
    login_response = test_client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert login_response.status_code == 204, f"Login failed: {login_response.text}"
    # Check that auth cookie is set
    assert "planned_auth" in test_client.cookies

    # Create default DayTemplate (required for scheduling)
    # Note: In production, this would be created by SheppardManager, but for e2e test
    # we create it directly since there's no API endpoint for template creation
    user_id = UUID(user_id_str)
    day_template_repo = DayTemplateRepository(user_id=user_id)
    default_template = DayTemplate(
        user_id=user_id,
        slug="default",
        alarm=Alarm(
            name="Default Alarm",
            time=time(7, 15),
            type=AlarmType.FIRM,
        ),
    )
    await day_template_repo.put(default_template)

    # Step 3: Load some data as the authenticated user
    # Schedule today (this will create a day and potentially tasks)
    schedule_response = test_client.put("/days/today/schedule")
    assert schedule_response.status_code == 200, (
        f"Schedule failed: {schedule_response.text}"
    )
    schedule_data = schedule_response.json()
    assert "day" in schedule_data
    assert schedule_data["day"]["user_id"] == user_id_str

    # Get context for today (loads day, tasks, calendar_entries, messages)
    context_response = test_client.get("/days/today/context")
    assert context_response.status_code == 200, (
        f"Get context failed: {context_response.text}"
    )
    context_data = context_response.json()
    assert "day" in context_data
    assert "tasks" in context_data
    assert "calendar_entries" in context_data
    assert "messages" in context_data
    assert context_data["day"]["user_id"] == user_id_str

    # Get templates
    templates_response = test_client.get("/days/templates")
    assert templates_response.status_code == 200, (
        f"Get templates failed: {templates_response.text}"
    )
    templates_data = templates_response.json()
    assert isinstance(templates_data, list)
    assert len(templates_data) > 0, "Should have at least one template (default)"

    # Step 4: Verify database state directly

    # Verify user in database
    user_from_db_after = await user_repo.get_by_email(email)
    assert user_from_db_after is not None
    assert user_from_db_after.id == user_id

    # Verify day was created in database
    day_repo = DayRepository(user_id=user_id)
    days = await day_repo.all()
    assert len(days) > 0, "At least one day should exist after scheduling"

    # Find the scheduled day
    scheduled_day = None
    for day in days:
        if day.user_id == user_id:
            scheduled_day = day
            break

    assert scheduled_day is not None, "Scheduled day should exist in database"
    assert scheduled_day.user_id == user_id
    assert scheduled_day.status in [
        DayStatus.SCHEDULED,
        DayStatus.COMPLETE,
        DayStatus.IN_PROGRESS,
    ], (
        f"Day status should be SCHEDULED, COMPLETE, or IN_PROGRESS, got {scheduled_day.status}"
    )

    # Verify day template exists in database
    day_template_repo = DayTemplateRepository(user_id=user_id)
    templates = await day_template_repo.all()
    assert len(templates) > 0, "At least one day template should exist"

    # Verify default template exists
    default_template = None
    for template in templates:
        if template.slug == "default":
            default_template = template
            break

    assert default_template is not None, "Default template should exist"
    assert default_template.user_id == user_id

    # Verify the scheduled day references a template
    if scheduled_day.template:
        template_ids = [t.id for t in templates]
        assert scheduled_day.template.id in template_ids, (
            "Day should reference an existing template"
        )
