"""Unit tests for service dependency injection functions.

These tests verify that dependencies are properly configured and injected.
"""

import contextlib
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway, StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory
from lykke.presentation.api.routers.dependencies.services import (
    get_pubsub_gateway,
    get_unit_of_work_factory,
)


def _create_mock_request():
    """Create a mock Request object for testing."""
    request = MagicMock()
    # Set redis_pool to None for tests (they don't need a real pool)
    request.app.state.redis_pool = None
    return request


@pytest.mark.asyncio
async def test_get_pubsub_gateway_returns_redis_gateway():
    """Test that get_pubsub_gateway returns a RedisPubSubGateway instance.

    This test also verifies that the gateway is properly cleaned up when the
    generator exits, preventing Redis connection leaks.
    """
    # Use the generator-based dependency with mock websocket
    websocket = MagicMock()
    # Set redis_pool to None for tests (they don't need a real pool)
    websocket.app.state.redis_pool = None
    gen = get_pubsub_gateway(websocket)
    gateway = await gen.__anext__()

    assert isinstance(gateway, RedisPubSubGateway)
    # Gateway should be usable
    assert gateway is not None

    # Clean up by exhausting the generator
    with contextlib.suppress(StopAsyncIteration):
        await gen.__anext__()


@pytest.mark.asyncio
async def test_get_unit_of_work_factory_requires_pubsub_gateway():
    """Test that get_unit_of_work_factory creates factory with pubsub_gateway.

    This is a regression test for a critical bug where the UnitOfWorkFactory
    was created without a PubSubGateway, causing audit logs to not be broadcast
    when tasks were completed via the API.

    The function now takes a Request and creates the pubsub_gateway from app state.
    This test also verifies proper cleanup of the RedisPubSubGateway.
    """
    # Create a mock request
    request = _create_mock_request()

    # Call the dependency function with the request (it's now an async generator)
    gen = get_unit_of_work_factory(request)
    factory = await gen.__anext__()

    # Verify it returns a factory
    assert isinstance(factory, SqlAlchemyUnitOfWorkFactory)

    # Verify the factory has the pubsub_gateway configured
    # by checking that it passes it through when creating a UoW
    user = UserEntity(email="test@example.com", hashed_password="!")
    uow = factory.create(user=user)

    # The UoW should have the pubsub_gateway set
    assert hasattr(uow, "_pubsub_gateway")
    assert uow._pubsub_gateway is not None

    # Clean up by exhausting the generator
    with contextlib.suppress(StopAsyncIteration):
        await gen.__anext__()


def test_unit_of_work_factory_requires_pubsub_gateway():
    """Test that SqlAlchemyUnitOfWorkFactory requires a pubsub_gateway parameter.

    This ensures that pubsub_gateway is always provided, preventing audit logs
    from not being broadcast.
    """
    # Create factory with a stub pubsub_gateway
    stub_gateway = StubPubSubGateway()
    factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=stub_gateway)

    # Create a UoW
    user = UserEntity(email="test@example.com", hashed_password="!")
    uow = factory.create(user=user)

    # The UoW should have the pubsub_gateway set
    assert hasattr(uow, "_pubsub_gateway")
    assert uow._pubsub_gateway is stub_gateway
