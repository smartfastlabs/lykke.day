"""Test that PubSub gateway cleanup works correctly in dependency injection.

This test verifies the fix for a critical bug where RedisPubSubGateway instances
were created for each request/WebSocket connection but never cleaned up, causing
Redis connection leaks.
"""

import pytest

from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.presentation.api.routers.dependencies.services import get_pubsub_gateway


@pytest.mark.asyncio
async def test_pubsub_gateway_cleanup_is_called():
    """Test that the gateway's close() method is called when the generator exits.

    This simulates what FastAPI does when using a generator-based dependency:
    1. Call the generator to get the gateway
    2. Use the gateway during the request/WebSocket connection
    3. Exit the generator, which triggers the finally block and calls close()
    """
    cleanup_called = False

    # Create the async generator
    gen = get_pubsub_gateway()

    # Get the gateway (simulates FastAPI calling the dependency)
    gateway = await gen.__anext__()

    # Verify it's the right type
    assert isinstance(gateway, RedisPubSubGateway)

    # Verify the gateway is usable (hasn't been closed yet)
    assert gateway._redis is None  # Lazy initialization

    # Monkey-patch close() to track if it's called
    original_close = gateway.close

    async def tracked_close():
        nonlocal cleanup_called
        cleanup_called = True
        await original_close()

    gateway.close = tracked_close

    # Simulate request/WebSocket handling
    # In real usage, the gateway would be used here

    # Close the generator (simulates FastAPI cleaning up after request)
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass  # Expected - generator is exhausted

    # Verify cleanup was called
    assert cleanup_called, "Gateway close() should be called when generator exits"


@pytest.mark.asyncio
async def test_pubsub_gateway_cleanup_on_exception():
    """Test that cleanup happens even if an exception occurs during request handling.

    This ensures that Redis connections are not leaked even when errors occur.
    """
    cleanup_called = False

    # Create the async generator
    gen = get_pubsub_gateway()

    try:
        # Get the gateway
        gateway = await gen.__anext__()

        # Monkey-patch close() to track if it's called
        original_close = gateway.close

        async def tracked_close():
            nonlocal cleanup_called
            cleanup_called = True
            await original_close()

        gateway.close = tracked_close

        # Simulate an error during request handling
        raise ValueError("Simulated request error")

    except ValueError:
        pass  # Expected error
    finally:
        # Clean up the generator (FastAPI does this automatically)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    # Verify cleanup was still called despite the exception
    assert cleanup_called, "Gateway close() should be called even when exception occurs"


@pytest.mark.asyncio
async def test_multiple_gateway_instances_are_independent():
    """Test that each call to get_pubsub_gateway() creates a new instance.

    This verifies that each request/WebSocket gets its own gateway instance,
    which is important for proper connection management.
    """
    gateways = []

    # Simulate two concurrent requests
    gen1 = get_pubsub_gateway()
    gateway1 = await gen1.__anext__()
    gateways.append(gateway1)

    gen2 = get_pubsub_gateway()
    gateway2 = await gen2.__anext__()
    gateways.append(gateway2)

    # Verify they are different instances
    assert len(gateways) == 2
    assert gateways[0] is not gateways[1]
    assert isinstance(gateways[0], RedisPubSubGateway)
    assert isinstance(gateways[1], RedisPubSubGateway)

    # Clean up both generators
    for gen in [gen1, gen2]:
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass
