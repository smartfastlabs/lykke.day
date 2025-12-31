"""Unit tests for SheppardManager."""

import asyncio
from uuid import uuid4

import pytest
from dobles import allow

from planned.application.services import SheppardManager


@pytest.mark.asyncio
async def test_get_service_for_user_not_found():
    """Test get_service_for_user returns None when service doesn't exist."""
    manager = SheppardManager()
    user_id = uuid4()

    result = manager.get_service_for_user(user_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_service_for_user_returns_service():
    """Test get_service_for_user returns service when it exists."""
    from planned.application.services import SheppardService
    from planned.domain.entities import Day, DayContext, DayStatus
    from planned.infrastructure.repositories import (
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        TaskRepository,
    )
    from planned.infrastructure.utils.dates import get_current_date

    manager = SheppardManager()
    user_id = uuid4()

    # Create a minimal service for testing
    day = Day(
        user_id=user_id,
        date=get_current_date(),
        status=DayStatus.UNSCHEDULED,
    )
    ctx = DayContext(day=day, tasks=[], events=[], messages=[])
    
    day_svc = None  # We'll skip full initialization for unit tests
    mock_service = object()  # Simplified mock
    
    # Create a cancelled task to avoid actual execution
    task = asyncio.create_task(asyncio.sleep(0))
    task.cancel()
    
    manager._services[user_id] = (mock_service, task)

    result = manager.get_service_for_user(user_id)

    assert result is mock_service


@pytest.mark.asyncio
async def test_stop_service_for_user_removes_service():
    """Test _stop_service_for_user removes service from manager."""
    from planned.application.services import SheppardService
    from planned.domain.entities import Day, DayContext, DayStatus
    from planned.infrastructure.repositories import (
        DayRepository,
        DayTemplateRepository,
        EventRepository,
        MessageRepository,
        TaskRepository,
    )
    from planned.infrastructure.utils.dates import get_current_date

    manager = SheppardManager()
    user_id = uuid4()

    # Create a mock service
    day = Day(
        user_id=user_id,
        date=get_current_date(),
        status=DayStatus.UNSCHEDULED,
    )
    
    # Create a minimal service mock
    mock_service = object()
    
    # Create a cancelled task
    task = asyncio.create_task(asyncio.sleep(0))
    task.cancel()
    
    manager._services[user_id] = (mock_service, task)

    # Mock the service.stop method if it's an actual service
    if hasattr(mock_service, "stop"):
        mock_service.stop = lambda: None

    await manager._stop_service_for_user(user_id)

    assert user_id not in manager._services


@pytest.mark.asyncio
async def test_stop_service_for_user_handles_missing_service():
    """Test _stop_service_for_user handles missing service gracefully."""
    manager = SheppardManager()
    user_id = uuid4()

    # Should not raise an exception
    await manager._stop_service_for_user(user_id)

    assert user_id not in manager._services


@pytest.mark.asyncio
async def test_start_stops_if_already_running(mock_user_repo):
    """Test start handles case when already running."""
    from planned.infrastructure.repositories import UserRepository

    manager = SheppardManager()
    manager._is_running = True

    # Should return early without error
    await manager.start()

    assert manager._is_running is True


@pytest.mark.asyncio
async def test_stop_idempotent():
    """Test stop can be called multiple times safely."""
    manager = SheppardManager()
    manager._is_running = False

    # Should not raise an exception
    await manager.stop()

    assert manager._is_running is False


@pytest.mark.asyncio
async def test_ensure_service_for_user_raises_if_cannot_start(mock_user_repo):
    """Test ensure_service_for_user raises RuntimeError if service cannot be started."""
    manager = SheppardManager()
    user_id = uuid4()

    # Mock _start_service_for_user to not actually start
    async def mock_start(uuid):
        # Don't actually start, simulate failure
        pass

    manager._start_service_for_user = mock_start

    with pytest.raises(RuntimeError) as exc_info:
        await manager.ensure_service_for_user(user_id)
    
    assert "Failed to start" in str(exc_info.value)
