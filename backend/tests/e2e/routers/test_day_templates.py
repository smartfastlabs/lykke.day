"""E2E tests for day-templates router endpoints."""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_list_day_templates(authenticated_client):
    """Test listing day templates."""
    client, user = await authenticated_client()

    response = client.get("/day-templates/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    # Should have at least the default template
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_get_day_template(authenticated_client):
    """Test getting a single day template by UUID."""
    client, user = await authenticated_client()

    # First, list templates to get a UUID
    list_response = client.get("/day-templates/")
    assert list_response.status_code == 200
    templates = list_response.json()["items"]
    template_id = templates[0]["id"]

    # Get the specific template
    response = client.get(f"/day-templates/{template_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert "slug" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_get_day_template_not_found(authenticated_client):
    """Test getting a non-existent day template returns 404."""
    client, user = await authenticated_client()

    fake_id = uuid4()
    response = client.get(f"/day-templates/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_day_template(authenticated_client):
    """Test creating a new day template."""
    client, user = await authenticated_client()

    template_data = {
        "user_id": str(user.id),
        "slug": "test-template",
        "alarm": {
            "name": "Test Alarm",
            "time": "08:00:00",
            "type": "GENTLE",
        },
    }

    response = client.post("/day-templates/", json=template_data)

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-template"
    assert data["user_id"] == str(user.id)
    assert data["alarm"]["name"] == "Test Alarm"


@pytest.mark.asyncio
async def test_update_day_template(authenticated_client):
    """Test updating an existing day template."""
    client, user = await authenticated_client()

    # First, create a template
    template_data = {
        "user_id": str(user.id),
        "slug": "update-test",
    }
    create_response = client.post("/day-templates/", json=template_data)
    assert create_response.status_code == 200
    template_id = create_response.json()["id"]

    # Update the template
    update_data = {
        "user_id": str(user.id),
        "slug": "update-test",
        "icon": "test-icon",
    }
    response = client.put(f"/day-templates/{template_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert data["icon"] == "test-icon"


@pytest.mark.asyncio
async def test_update_day_template_not_found(authenticated_client):
    """Test updating a non-existent day template returns 404."""
    client, user = await authenticated_client()

    fake_id = uuid4()
    update_data = {
        "user_id": str(user.id),
        "slug": "does-not-exist",
    }
    response = client.put(f"/day-templates/{fake_id}", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_day_template(authenticated_client):
    """Test deleting a day template."""
    client, user = await authenticated_client()

    # First, create a template
    template_data = {
        "user_id": str(user.id),
        "slug": "delete-test",
    }
    create_response = client.post("/day-templates/", json=template_data)
    assert create_response.status_code == 200
    template_id = create_response.json()["id"]

    # Delete the template
    response = client.delete(f"/day-templates/{template_id}")

    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/day-templates/{template_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_day_template_not_found(authenticated_client):
    """Test deleting a non-existent day template returns 404."""
    client, user = await authenticated_client()

    fake_id = uuid4()
    response = client.delete(f"/day-templates/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_day_templates_pagination(authenticated_client):
    """Test pagination parameters for listing day templates."""
    client, user = await authenticated_client()

    # Create multiple templates
    for i in range(3):
        template_data = {
            "user_id": str(user.id),
            "slug": f"pagination-test-{i}",
        }
        client.post("/day-templates/", json=template_data)

    # Test pagination
    response = client.get("/day-templates/?limit=2&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data


@pytest.mark.asyncio
async def test_add_routine_to_day_template(authenticated_client):
    """Test adding a routine to a day template."""
    client, user = await authenticated_client()

    # Create a day template
    from planned.domain.data_objects import DayTemplate
    from planned.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplate(
        user_id=user.id,
        slug="routine-test",
        routine_ids=[],
    )
    day_template = await day_template_repo.put(day_template)

    # Create a routine
    from planned.domain.entities import RoutineEntity
    from planned.domain.value_objects.routine import RoutineSchedule
    from planned.domain.value_objects.task import TaskCategory, TaskFrequency
    from planned.infrastructure.repositories import RoutineRepository

    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    # Add routine to day template
    response = client.post(
        f"/day-templates/{day_template.id}/routines",
        json={"routine_id": str(routine.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert str(routine.id) in data["routine_ids"]


@pytest.mark.asyncio
async def test_add_duplicate_routine_to_day_template(authenticated_client):
    """Test adding a duplicate routine to a day template returns error."""
    client, user = await authenticated_client()

    # Create a day template with a routine already attached
    from planned.domain.data_objects import DayTemplate
    from planned.domain.entities import RoutineEntity
    from planned.domain.value_objects.routine import RoutineSchedule
    from planned.domain.value_objects.task import TaskCategory, TaskFrequency
    from planned.infrastructure.repositories import (
        DayTemplateRepository,
        RoutineRepository,
    )

    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplate(
        user_id=user.id,
        slug="duplicate-test",
        routine_ids=[routine.id],
    )
    day_template = await day_template_repo.put(day_template)

    # Try to add the same routine again
    response = client.post(
        f"/day-templates/{day_template.id}/routines",
        json={"routine_id": str(routine.id)},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_remove_routine_from_day_template(authenticated_client):
    """Test removing a routine from a day template."""
    client, user = await authenticated_client()

    # Create a routine
    from planned.domain.entities import RoutineEntity
    from planned.domain.value_objects.routine import RoutineSchedule
    from planned.domain.value_objects.task import TaskCategory, TaskFrequency
    from planned.infrastructure.repositories import RoutineRepository

    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RoutineSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    # Create a day template with the routine attached
    from planned.domain.data_objects import DayTemplate
    from planned.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplate(
        user_id=user.id,
        slug="remove-test",
        routine_ids=[routine.id],
    )
    day_template = await day_template_repo.put(day_template)

    # Remove routine from day template
    response = client.delete(
        f"/day-templates/{day_template.id}/routines/{routine.id}",
    )

    assert response.status_code == 200
    data = response.json()
    assert str(routine.id) not in data["routine_ids"]


@pytest.mark.asyncio
async def test_remove_nonexistent_routine_from_day_template(authenticated_client):
    """Test removing a routine that doesn't exist from a day template returns error."""
    client, user = await authenticated_client()

    # Create a day template without any routines
    from planned.domain.data_objects import DayTemplate
    from planned.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplate(
        user_id=user.id,
        slug="remove-nonexistent-test",
        routine_ids=[],
    )
    day_template = await day_template_repo.put(day_template)

    # Try to remove a routine that doesn't exist
    fake_routine_id = uuid4()
    response = client.delete(
        f"/day-templates/{day_template.id}/routines/{fake_routine_id}",
    )

    assert response.status_code == 404
