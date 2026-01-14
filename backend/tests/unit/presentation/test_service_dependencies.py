"""Unit tests for service dependency injection functions.

These tests verify that dependencies are properly configured and injected.
"""

import pytest

from lykke.infrastructure.gateways import RedisPubSubGateway, StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory
from lykke.presentation.api.routers.dependencies.services import (
    get_pubsub_gateway,
    get_unit_of_work_factory,
)


def test_get_pubsub_gateway_returns_redis_gateway():
    """Test that get_pubsub_gateway returns a RedisPubSubGateway instance."""
    gateway = get_pubsub_gateway()
    
    assert isinstance(gateway, RedisPubSubGateway)


def test_get_unit_of_work_factory_requires_pubsub_gateway():
    """Test that get_unit_of_work_factory accepts a pubsub_gateway parameter.
    
    This is a regression test for a critical bug where the UnitOfWorkFactory
    was created without a PubSubGateway, causing audit logs to not be broadcast
    when tasks were completed via the API.
    
    The bug was that get_unit_of_work_factory() didn't accept a pubsub_gateway
    parameter, so it always created SqlAlchemyUnitOfWorkFactory() without one.
    This meant that _broadcast_audit_logs() would return early because
    self._pubsub_gateway was None.
    """
    # Create a mock pubsub gateway
    pubsub_gateway = get_pubsub_gateway()
    
    # Call the dependency function with the gateway
    factory = get_unit_of_work_factory(pubsub_gateway=pubsub_gateway)
    
    # Verify it returns a factory
    assert isinstance(factory, SqlAlchemyUnitOfWorkFactory)
    
    # Verify the factory has the pubsub_gateway configured
    # by checking that it passes it through when creating a UoW
    from uuid import uuid4
    uow = factory.create(user_id=uuid4())
    
    # The UoW should have the pubsub_gateway set
    assert hasattr(uow, "_pubsub_gateway")
    assert uow._pubsub_gateway is pubsub_gateway


def test_unit_of_work_factory_requires_pubsub_gateway():
    """Test that SqlAlchemyUnitOfWorkFactory requires a pubsub_gateway parameter.
    
    This ensures that pubsub_gateway is always provided, preventing audit logs
    from not being broadcast.
    """
    # Create factory with a stub pubsub_gateway
    stub_gateway = StubPubSubGateway()
    factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=stub_gateway)
    
    # Create a UoW
    from uuid import uuid4
    uow = factory.create(user_id=uuid4())
    
    # The UoW should have the pubsub_gateway set
    assert hasattr(uow, "_pubsub_gateway")
    assert uow._pubsub_gateway is stub_gateway
