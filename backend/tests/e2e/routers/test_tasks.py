"""E2E tests for task routes."""

import pytest
from fastapi import status
from httpx import AsyncClient

from lykke.domain.value_objects.task import TaskStatus


@pytest.mark.asyncio
async def test_complete_task_action(
    test_client: AsyncClient,
    test_user,
    test_task,
):
    """Test completing a task via the API.
    
    This is a regression test for a bug where completing a task would fail with:
    ValueError: 'TaskStatus.NOT_STARTED' is not a valid TaskStatus
    
    The bug was caused by using str(enum) instead of enum.value when serializing
    to the database, which produced 'TaskStatus.NOT_STARTED' instead of 'NOT_STARTED'.
    """
    # Verify task starts with NOT_STARTED status
    assert test_task.status == TaskStatus.NOT_STARTED
    
    # Complete the task via API
    response = await test_client.post(
        f"/api/tasks/{test_task.id}/actions",
        json={"type": "COMPLETE"},
    )
    
    # Verify the response is successful
    assert response.status_code == status.HTTP_200_OK
    
    # Verify the task status changed to COMPLETE
    data = response.json()
    assert data["status"] == "COMPLETE"
    assert data["id"] == str(test_task.id)
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_punt_task_action(
    test_client: AsyncClient,
    test_user,
    test_task,
):
    """Test punting a task via the API."""
    # Verify task starts with NOT_STARTED status
    assert test_task.status == TaskStatus.NOT_STARTED
    
    # Punt the task via API
    response = await test_client.post(
        f"/api/tasks/{test_task.id}/actions",
        json={"type": "PUNT"},
    )
    
    # Verify the response is successful
    assert response.status_code == status.HTTP_200_OK
    
    # Verify the task status changed to PUNT
    data = response.json()
    assert data["status"] == "PUNT"
    assert data["id"] == str(test_task.id)
