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
        "tasks": ["task1", "task2"],
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
    assert len(data["tasks"]) == 2
    assert data["alarm"]["name"] == "Test Alarm"


@pytest.mark.asyncio
async def test_update_day_template(authenticated_client):
    """Test updating an existing day template."""
    client, user = await authenticated_client()

    # First, create a template
    template_data = {
        "user_id": str(user.id),
        "slug": "update-test",
        "tasks": ["task1"],
    }
    create_response = client.post("/day-templates/", json=template_data)
    assert create_response.status_code == 200
    template_id = create_response.json()["id"]

    # Update the template
    update_data = {
        "user_id": str(user.id),
        "slug": "update-test",
        "tasks": ["task1", "task2", "task3"],
        "icon": "test-icon",
    }
    response = client.put(f"/day-templates/{template_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert len(data["tasks"]) == 3
    assert data["icon"] == "test-icon"


@pytest.mark.asyncio
async def test_update_day_template_not_found(authenticated_client):
    """Test updating a non-existent day template returns 404."""
    client, user = await authenticated_client()

    fake_id = uuid4()
    update_data = {
        "user_id": str(user.id),
        "slug": "does-not-exist",
        "tasks": [],
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
        "tasks": [],
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
            "tasks": [],
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

