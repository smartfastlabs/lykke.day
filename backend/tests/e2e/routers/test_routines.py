"""E2E tests for routines router endpoints."""

from uuid import uuid4

import pytest

from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects.routine import RecurrenceSchedule
from lykke.domain.value_objects.task import TaskCategory, TaskFrequency
from lykke.infrastructure.repositories import RoutineRepository


@pytest.mark.asyncio
async def test_list_routines(authenticated_client):
    """Test listing routines."""
    client, user = await authenticated_client()

    # Create a routine via repository (since router is read-only)
    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    await routine_repo.put(routine)

    response = client.post("/routines/", json={"limit": 50, "offset": 0})

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
async def test_get_routine(authenticated_client):
    """Test getting a single routine by UUID."""
    client, user = await authenticated_client()

    # Create a routine via repository
    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Get Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    # Get the specific routine
    response = client.get(f"/routines/{routine.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(routine.id)
    assert data["name"] == "Get Test Routine"
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_routine_not_found(authenticated_client):
    """Test getting a non-existent routine returns 404."""
    client, user = await authenticated_client()

    fake_id = uuid4()
    response = client.get(f"/routines/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_routine(authenticated_client):
    """Test creating a routine via router."""
    client, user = await authenticated_client()

    routine_data = {
        "user_id": str(user.id),
        "name": "Should Not Work",
        "category": "HOUSE",
        "description": "Test",
        "routine_schedule": {"frequency": "DAILY"},
        "tasks": [],
    }

    response = client.post("/routines/create", json=routine_data)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_routine_with_tasks(authenticated_client):
    """Create routine and ensure attached tasks are persisted."""
    client, user = await authenticated_client()

    task_definition_id = str(uuid4())
    routine_data = {
        "user_id": str(user.id),
        "name": "Morning",
        "category": "HOUSE",
        "description": "With tasks",
        "routine_schedule": {"frequency": "DAILY"},
        "tasks": [
            {
                "task_definition_id": task_definition_id,
                "name": "Make bed",
                "schedule": {
                    "timing_type": "FIXED_TIME",
                    "start_time": "07:30:00",
                },
            }
        ],
    }

    response = client.post("/routines/create", json=routine_data)

    assert response.status_code == 201
    body = response.json()
    assert body["tasks"]
    assert body["tasks"][0]["task_definition_id"] == task_definition_id
    assert body["tasks"][0]["name"] == "Make bed"
    assert body["tasks"][0]["schedule"]["start_time"] == "07:30:00"


@pytest.mark.asyncio
async def test_update_routine(authenticated_client):
    """Test updating a routine via router."""
    client, user = await authenticated_client()

    # Create a routine via repository
    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    update_data = {
        "user_id": str(user.id),
        "name": "Updated Name",
        "category": "HOUSE",
        "description": "Test",
        "routine_schedule": {"frequency": "DAILY"},
        "tasks": [],
    }

    response = client.put(f"/routines/{routine.id}", json=update_data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_routine(authenticated_client):
    """Test deleting a routine via router."""
    client, user = await authenticated_client()

    # Create a routine via repository
    routine_repo = RoutineRepository(user_id=user.id)
    routine = RoutineEntity(
        id=uuid4(),
        user_id=user.id,
        name="Test Routine",
        category=TaskCategory.HOUSE,
        description="Test description",
        routine_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
        tasks=[],
    )
    routine = await routine_repo.put(routine)

    response = client.delete(f"/routines/{routine.id}")

    assert response.status_code in [204, 200]


@pytest.mark.asyncio
async def test_list_routines_pagination(authenticated_client):
    """Test pagination parameters for listing routines."""
    client, user = await authenticated_client()

    # Create multiple routines via repository
    routine_repo = RoutineRepository(user_id=user.id)
    for i in range(3):
        routine = RoutineEntity(
            id=uuid4(),
            user_id=user.id,
            name=f"Pagination Test {i}",
            category=TaskCategory.HOUSE,
            description="Test description",
            routine_schedule=RecurrenceSchedule(frequency=TaskFrequency.DAILY),
            tasks=[],
        )
        await routine_repo.put(routine)

    # Test pagination
    response = client.post("/routines/", json={"limit": 2, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data

