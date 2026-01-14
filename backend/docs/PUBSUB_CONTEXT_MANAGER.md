# PubSub Context Manager Enhancement

## Summary

Updated the Redis PubSub system to use async context managers and support bidirectional communication (sending and receiving messages through subscriptions).

## Changes Made

### 1. Protocol Updates (`application/gateways/pubsub_protocol.py`)

**Before:**
```python
async def subscribe_to_user_channel(user_id, channel_type) -> PubSubSubscription:
    """Returns a subscription object"""
    ...
```

**After:**
```python
def subscribe_to_user_channel(user_id, channel_type) -> PubSubSubscription:
    """Returns a context manager for subscribing"""
    ...

class PubSubSubscription(Protocol):
    """Protocol that supports async context manager"""
    
    async def __aenter__(self) -> Self: ...
    async def __aexit__(...) -> None: ...
    async def get_message(timeout) -> dict | None: ...
    async def send_message(message: dict) -> None: ...  # NEW
    async def close(self) -> None: ...
```

### 2. Implementation Updates (`infrastructure/gateways/redis_pubsub.py`)

#### Added Context Manager Support

- Created `_SubscriptionContextManager` class that implements the protocol
- Handles async initialization of Redis subscription
- Automatically cleans up resources on exit

#### Added Bidirectional Communication

- `RedisSubscription` now accepts a Redis client for publishing
- Added `send_message()` method to subscriptions
- Subscribers can now both receive and send messages

### 3. Usage Changes

**Old Pattern:**
```python
subscription = await gateway.subscribe_to_user_channel(user_id, "auditlog")
try:
    message = await subscription.get_message()
finally:
    await subscription.close()
```

**New Pattern:**
```python
async with gateway.subscribe_to_user_channel(user_id, "auditlog") as sub:
    # Receive messages
    message = await sub.get_message()
    
    # Send messages (NEW!)
    await sub.send_message({"response": "ok"})
# Automatic cleanup on exit
```

### 4. Test Updates

All tests updated to use the new context manager pattern:
- 7 original tests updated
- 5 new tests added for sending functionality
- All 12 tests passing

#### New Test Coverage:
- `test_send_message_through_subscription` - Basic sending
- `test_bidirectional_communication` - Two-way communication
- `test_send_message_after_close_raises_error` - Error handling
- `test_send_and_publish_are_equivalent` - Consistency check
- `test_context_manager_cleanup` - Resource cleanup

### 5. Documentation Updates

Updated `docs/PUBSUB_SYSTEM.md` with:
- Context manager usage examples
- Bidirectional communication patterns
- WebSocket integration example using new API
- API reference for new methods

## Benefits

1. **Cleaner Code**: Context managers ensure automatic cleanup
2. **Type Safety**: Maintained full mypy compatibility
3. **Bidirectional**: Subscriptions can now send and receive
4. **Flexible**: Can still use manual `close()` if needed
5. **Ergonomic**: Natural Python idiom for resource management

## Migration Guide

### For Simple Receiving:

```python
# Before
subscription = await gateway.subscribe_to_user_channel(user_id, "auditlog")
try:
    msg = await subscription.get_message()
finally:
    await subscription.close()

# After
async with gateway.subscribe_to_user_channel(user_id, "auditlog") as sub:
    msg = await sub.get_message()
```

### For WebSocket Handlers:

```python
async with gateway.subscribe_to_user_channel(user_id, "auditlog") as sub:
    while True:
        # Receive from Redis
        redis_msg = await sub.get_message(timeout=0.1)
        if redis_msg:
            await websocket.send_json(redis_msg)
        
        # Receive from WebSocket and broadcast
        ws_msg = await websocket.receive_json()
        await sub.send_message({"from_client": ws_msg})
```

## Backward Compatibility

The changes are **not backward compatible** - all code using `subscribe_to_user_channel` must be updated to:
1. Use `async with` instead of `await`
2. Remove manual `await subscription.close()` calls

However, the integration tests in the codebase have been updated, so there should be no existing code to migrate except for future WebSocket implementations.

## Type Safety

All changes pass strict mypy type checking:
```bash
poetry run mypy lykke/infrastructure/gateways/redis_pubsub.py lykke/application/gateways/pubsub_protocol.py
# Success: no issues found in 2 source files
```

## Testing

Run tests with:
```bash
# All PubSub tests
poetry run pytest tests/unit/gateways/test_redis_pubsub*.py -v

# Results: 12/12 tests passing ✓
```
