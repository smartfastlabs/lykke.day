"""E2E tests for routine definitions router endpoints."""

from uuid import uuid4

import pytest

from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects.routine_definition import RecurrenceSchedule
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
from lykke.infrastructure.repositories import RoutineDefinitionRepository


@pytest.mark.asyncio
async def test_list_routine_definitions(authenticated_client):
    """Test listing routine definitions."""
    client, user = await authenticated_client()

    # Create a routine definition via repository (since router is read-only)
    routine_definition_repo = RoutineDefinitionRepository(user=user)
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
    await routine_definition_repo.put(routine_definition)

    response = client.post(
        "/routine-definitions/", json={"limit": 50, "offset": 0}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_get_routine_definition(authenticated_client):
    """Test getting a single routine definition by UUID."""
    client, user = await authenticated_client()

    # Create a routine definition via repository
    routine_definition_repo = RoutineDefinitionRepository(user=user)
    routine_definition = RoutineDefinitionEntity(
        id=uuid4(),
        user_id=user.id,
        name="Get Test Routine Definition",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_definition_schedule=RecurrenceSchedule(
            frequency=TaskFrequency.DAILY
        ),
        tasks=[],
    )
    routine_definition = await routine_definition_repo.put(routine_definition)

    # Get the specific routine definition
    response = client.get(f"/routine-definitions/{routine_definition.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(routine_definition.id)
    assert data["name"] == "Get Test Routine Definition"
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_routine_definition_not_found(authenticated_client):
    """Test getting a non-existent routine definition returns 404."""
    client, _user = await authenticated_client()

    fake_id = uuid4()
    response = client.get(f"/routine-definitions/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_routine_definition(authenticated_client):
    """Test creating a routine definition via router."""
    client, user = await authenticated_client()

    routine_definition_data = {
        "user_id": str(user.id),
        "name": "Should Not Work",
        "category": "HOUSE",
        "description": "Test",
        "routine_definition_schedule": {"frequency": "DAILY"},
        "tasks": [],
    }

    response = client.post(
        "/routine-definitions/create", json=routine_definition_data
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_routine_definition_with_tasks(authenticated_client):
    """Create routine definition and ensure attached tasks are persisted."""
    client, user = await authenticated_client()

    task_definition_id = str(uuid4())
    routine_definition_data = {
        "user_id": str(user.id),
        "name": "Morning",
        "category": "HOUSE",
        "description": "With tasks",
        "routine_definition_schedule": {"frequency": "DAILY"},
        "tasks": [
            {
                "task_definition_id": task_definition_id,
                "name": "Make bed",
                "time_window": {"start_time": "07:30:00"},
            }
        ],
    }

    response = client.post(
        "/routine-definitions/create", json=routine_definition_data
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tasks"]
    assert body["tasks"][0]["task_definition_id"] == task_definition_id
    assert body["tasks"][0]["name"] == "Make bed"
    assert body["tasks"][0]["time_window"]["start_time"] == "07:30:00"


@pytest.mark.asyncio
async def test_update_routine_definition(authenticated_client):
    """Test updating a routine definition via router."""
    client, user = await authenticated_client()

    # Create a routine definition via repository
    routine_definition_repo = RoutineDefinitionRepository(user=user)
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

    update_data = {
        "user_id": str(user.id),
        "name": "Updated Name",
        "category": "HOUSE",
        "description": "Test",
        "routine_definition_schedule": {"frequency": "DAILY"},
        "tasks": [],
    }

    response = client.put(
        f"/routine-definitions/{routine_definition.id}",
        json=update_data,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_routine_definition(authenticated_client):
    """Test deleting a routine definition via router."""
    client, user = await authenticated_client()

    # Create a routine definition via repository
    routine_definition_repo = RoutineDefinitionRepository(user=user)
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

    response = client.delete(
        f"/routine-definitions/{routine_definition.id}"
    )

    assert response.status_code in [204, 200]


@pytest.mark.asyncio
async def test_list_routine_definitions_pagination(authenticated_client):
    """Test pagination parameters for listing routine definitions."""
    client, user = await authenticated_client()

    # Create multiple routine definitions via repository
    routine_definition_repo = RoutineDefinitionRepository(user=user)
    for i in range(3):
        routine_definition = RoutineDefinitionEntity(
            id=uuid4(),
            user_id=user.id,
            name=f"Pagination Test Definition {i}",
            category=TaskCategory.HOUSE,
            description="Test description",
            routine_definition_schedule=RecurrenceSchedule(
                frequency=TaskFrequency.DAILY
            ),
            tasks=[],
        )
        await routine_definition_repo.put(routine_definition)

    # Test pagination
    response = client.post(
        "/routine-definitions/", json={"limit": 2, "offset": 0}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data
