"""E2E tests for day-templates router endpoints."""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_list_day_templates(authenticated_client):
    """Test listing day templates."""
    client, _user = await authenticated_client()

    response = client.post("/day-templates/", json={"limit": 50, "offset": 0})

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
    client, _user = await authenticated_client()

    # First, list templates to get a UUID
    list_response = client.post("/day-templates/", json={"limit": 50, "offset": 0})
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
    client, _user = await authenticated_client()

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
    }

    response = client.post("/day-templates/create", json=template_data)

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-template"
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_update_day_template(authenticated_client):
    """Test updating an existing day template."""
    client, user = await authenticated_client()

    # First, create a template
    template_data = {
        "user_id": str(user.id),
        "slug": "update-test",
    }
    create_response = client.post("/day-templates/create", json=template_data)
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
    create_response = client.post("/day-templates/create", json=template_data)
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
    client, _user = await authenticated_client()

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
        client.post("/day-templates/create", json=template_data)

    # Test pagination
    response = client.post("/day-templates/", json={"limit": 2, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data


@pytest.mark.asyncio
async def test_add_routine_definition_to_day_template(authenticated_client):
    """Test adding a routine definition to a day template."""
    client, user = await authenticated_client()

    # Create a day template
    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="routine-test",
        routine_definition_ids=[],
    )
    day_template = await day_template_repo.put(day_template)

    # Create a routine definition
    from lykke.domain.entities import RoutineDefinitionEntity
    from lykke.domain.value_objects.routine import RecurrenceSchedule
    from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
    from lykke.infrastructure.repositories import RoutineDefinitionRepository

    routine_definition_repo = RoutineDefinitionRepository(user_id=user.id)
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine Definition",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_definition_schedule=RecurrenceSchedule(
            frequency=TaskFrequency.DAILY
        ),
        tasks=[],
    )
    routine_definition = await routine_definition_repo.put(routine_definition)

    # Add routine definition to day template
    response = client.post(
        f"/day-templates/{day_template.id}/routine-definitions",
        json={"routine_definition_id": str(routine_definition.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert str(routine_definition.id) in data["routine_definition_ids"]


@pytest.mark.asyncio
async def test_add_duplicate_routine_definition_to_day_template(authenticated_client):
    """Test adding a duplicate routine definition to a day template returns error."""
    client, user = await authenticated_client()

    # Create a day template with a routine definition already attached
    from lykke.domain.entities import RoutineDefinitionEntity
    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.domain.value_objects.routine import RecurrenceSchedule
    from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
    from lykke.infrastructure.repositories import (
        DayTemplateRepository,
        RoutineDefinitionRepository,
    )

    routine_definition_repo = RoutineDefinitionRepository(user_id=user.id)
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine Definition",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_definition_schedule=RecurrenceSchedule(
            frequency=TaskFrequency.DAILY
        ),
        tasks=[],
    )
    routine_definition = await routine_definition_repo.put(routine_definition)

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="duplicate-test",
        routine_definition_ids=[routine_definition.id],
    )
    day_template = await day_template_repo.put(day_template)

    # Try to add the same routine definition again
    response = client.post(
        f"/day-templates/{day_template.id}/routine-definitions",
        json={"routine_definition_id": str(routine_definition.id)},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_remove_routine_definition_from_day_template(authenticated_client):
    """Test removing a routine definition from a day template."""
    client, user = await authenticated_client()

    # Create a routine definition
    from lykke.domain.entities import RoutineDefinitionEntity
    from lykke.domain.value_objects.routine import RecurrenceSchedule
    from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
    from lykke.infrastructure.repositories import RoutineDefinitionRepository

    routine_definition_repo = RoutineDefinitionRepository(user_id=user.id)
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine Definition",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_definition_schedule=RecurrenceSchedule(
            frequency=TaskFrequency.DAILY
        ),
        tasks=[],
    )
    routine_definition = await routine_definition_repo.put(routine_definition)

    # Create a day template with the routine definition attached
    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="remove-test",
        routine_definition_ids=[routine_definition.id],
    )
    day_template = await day_template_repo.put(day_template)

    # Remove routine definition from day template
    response = client.delete(
        f"/day-templates/{day_template.id}/routine-definitions/{routine_definition.id}",
    )

    assert response.status_code == 200
    data = response.json()
    assert str(routine_definition.id) not in data["routine_definition_ids"]


@pytest.mark.asyncio
async def test_remove_nonexistent_routine_definition_from_day_template(
    authenticated_client,
):
    """Test removing a routine definition that doesn't exist from a day template returns error."""
    client, user = await authenticated_client()

    # Create a day template without any routine definitions
    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="remove-nonexistent-test",
        routine_definition_ids=[],
    )
    day_template = await day_template_repo.put(day_template)

    # Try to remove a routine definition that doesn't exist
    fake_routine_definition_id = uuid4()
    response = client.delete(
        f"/day-templates/{day_template.id}/routine-definitions/{fake_routine_definition_id}",
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_time_block_to_day_template_persists_to_database(
    authenticated_client,
):
    """Test that adding a time block to a day template persists to the database."""
    client, user = await authenticated_client()

    # Create a day template
    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="time-block-test",
        time_blocks=[],
    )
    day_template = await day_template_repo.put(day_template)

    # Create a time block definition
    from lykke.domain import value_objects
    from lykke.domain.entities import TimeBlockDefinitionEntity
    from lykke.domain.value_objects.time_block import TimeBlockCategory, TimeBlockType
    from lykke.infrastructure.repositories import TimeBlockDefinitionRepository

    time_block_def_repo = TimeBlockDefinitionRepository(user_id=user.id)
    time_block_def = TimeBlockDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Morning Work",
        description="Focused work time",
        type=TimeBlockType.WORK,
        category=TimeBlockCategory.WORK,
    )
    time_block_def = await time_block_def_repo.put(time_block_def)

    # Add time block to day template via API
    response = client.post(
        f"/day-templates/{day_template.id}/time-blocks",
        json={
            "time_block_definition_id": str(time_block_def.id),
            "start_time": "09:00:00",
            "end_time": "12:00:00",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["time_blocks"]) == 1
    assert data["time_blocks"][0]["time_block_definition_id"] == str(time_block_def.id)
    assert data["time_blocks"][0]["start_time"] == "09:00:00"
    assert data["time_blocks"][0]["end_time"] == "12:00:00"

    # Verify persistence by fetching the day template again from the database
    fetched_template = await day_template_repo.get(day_template.id)
    assert len(fetched_template.time_blocks) == 1
    assert fetched_template.time_blocks[0].time_block_definition_id == time_block_def.id
    assert str(fetched_template.time_blocks[0].start_time) == "09:00:00"
    assert str(fetched_template.time_blocks[0].end_time) == "12:00:00"


@pytest.mark.asyncio
async def test_remove_time_block_from_day_template_persists_to_database(
    authenticated_client,
):
    """Test that removing a time block from a day template persists to the database."""
    client, user = await authenticated_client()

    # Create a time block definition
    from lykke.domain import value_objects
    from lykke.domain.entities import TimeBlockDefinitionEntity
    from lykke.domain.value_objects.time_block import TimeBlockCategory, TimeBlockType
    from lykke.infrastructure.repositories import TimeBlockDefinitionRepository

    time_block_def_repo = TimeBlockDefinitionRepository(user_id=user.id)
    time_block_def = TimeBlockDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Afternoon Work",
        description="Afternoon focused work",
        type=TimeBlockType.WORK,
        category=TimeBlockCategory.WORK,
    )
    time_block_def = await time_block_def_repo.put(time_block_def)

    # Create a day template with a time block
    from datetime import time

    from lykke.domain.entities.day_template import DayTemplateEntity
    from lykke.infrastructure.repositories import DayTemplateRepository

    day_template_repo = DayTemplateRepository(user_id=user.id)
    day_template = DayTemplateEntity(
        user_id=user.id,
        slug="remove-time-block-test",
        time_blocks=[
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=time_block_def.id,
                start_time=time(14, 0, 0),
                end_time=time(17, 0, 0),
                name=time_block_def.name,
            )
        ],
    )
    day_template = await day_template_repo.put(day_template)

    # Verify it was created with the time block
    assert len(day_template.time_blocks) == 1

    # Remove time block from day template via API
    response = client.delete(
        f"/day-templates/{day_template.id}/time-blocks/{time_block_def.id}/14:00:00",
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["time_blocks"]) == 0

    # Verify persistence by fetching the day template again from the database
    fetched_template = await day_template_repo.get(day_template.id)
    assert len(fetched_template.time_blocks) == 0
