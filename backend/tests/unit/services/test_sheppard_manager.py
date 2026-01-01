"""Unit tests for SheppardManager."""

import asyncio
from uuid import uuid4

import pytest
from dobles import allow

from planned.application.services import SheppardManager


@pytest.fixture
def sheppard_manager(mock_uow_factory, mock_google_gateway, mock_web_push_gateway):
    """Create a SheppardManager with mocked dependencies."""
    return SheppardManager(
        uow_factory=mock_uow_factory,
        google_gateway=mock_google_gateway,
        web_push_gateway=mock_web_push_gateway,
    )


@pytest.mark.asyncio
async def test_get_service_for_user_not_found(sheppard_manager):
    """Test get_service_for_user returns None when service doesn't exist."""
    user_id = uuid4()

    result = sheppard_manager.get_service_for_user(user_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_service_for_user_returns_service(sheppard_manager):
    """Test get_service_for_user returns service when it exists."""
    user_id = uuid4()

    # Create a minimal service mock
    mock_service = object()

    # Create a cancelled task to avoid actual execution
    task = asyncio.create_task(asyncio.sleep(0))
    task.cancel()

    sheppard_manager._services[user_id] = (mock_service, task)

    result = sheppard_manager.get_service_for_user(user_id)

    assert result is mock_service


@pytest.mark.asyncio
async def test_stop_service_for_user_removes_service(sheppard_manager):
    """Test _stop_service_for_user removes service from manager."""
    user_id = uuid4()

    # Create a minimal service mock
    mock_service = object()

    # Create a cancelled task
    task = asyncio.create_task(asyncio.sleep(0))
    task.cancel()

    sheppard_manager._services[user_id] = (mock_service, task)

    await sheppard_manager._stop_service_for_user(user_id)

    assert user_id not in sheppard_manager._services


@pytest.mark.asyncio
async def test_stop_service_for_user_handles_missing_service(sheppard_manager):
    """Test _stop_service_for_user handles missing service gracefully."""
    user_id = uuid4()

    # Should not raise an exception
    await sheppard_manager._stop_service_for_user(user_id)

    assert user_id not in sheppard_manager._services


@pytest.mark.asyncio
async def test_start_stops_if_already_running(sheppard_manager):
    """Test start handles case when already running."""
    sheppard_manager._is_running = True

    # Should return early without error
    await sheppard_manager.start()

    assert sheppard_manager._is_running is True


@pytest.mark.asyncio
async def test_stop_idempotent(sheppard_manager):
    """Test stop can be called multiple times safely."""
    sheppard_manager._is_running = False

    # Should not raise an exception
    await sheppard_manager.stop()

    assert sheppard_manager._is_running is False


@pytest.mark.asyncio
async def test_ensure_service_for_user_raises_if_cannot_start(sheppard_manager):
    """Test ensure_service_for_user raises RuntimeError if service cannot be started."""
    user_id = uuid4()

    # Mock _start_service_for_user to not actually start
    async def mock_start(uuid):
        # Don't actually start, simulate failure
        pass

    sheppard_manager._start_service_for_user = mock_start

    with pytest.raises(RuntimeError) as exc_info:
        await sheppard_manager.ensure_service_for_user(user_id)

    assert "Failed to start" in str(exc_info.value)
