# Redis PubSub System for AuditLog Events

This document describes the Redis PubSub system that broadcasts AuditLog events in real-time.

## Overview

The system automatically publishes AuditLog entities to user-specific Redis channels whenever they are created and committed to the database. This enables real-time notifications and monitoring capabilities.

## Architecture

### Components

1. **PubSubGatewayProtocol** (`application/gateways/pubsub_protocol.py`)

   - Protocol (interface) defining the pub/sub operations
   - Methods for publishing and subscribing to user-specific channels

2. **RedisPubSubGateway** (`infrastructure/gateways/redis_pubsub.py`)

   - Redis implementation of the PubSubGatewayProtocol
   - Handles connection management and message serialization

3. **SqlAlchemyUnitOfWork** (`infrastructure/unit_of_work.py`)
   - Integrates PubSub broadcasting into the transaction lifecycle
   - Broadcasts AuditLog entities after successful commit

### Data Flow

```
1. Command creates AuditLogEntity
2. Entity added to UnitOfWork via create()
3. UnitOfWork tracks entity for broadcasting
4. Transaction commits successfully
5. AuditLog entity published to Redis channel: "auditlog:{user_id}"
6. Subscribers receive the message in real-time
```

## Channel Naming

Channels follow this pattern: `{channel_type}:{user_id}`

Examples:

- `auditlog:123e4567-e89b-12d3-a456-426614174000`
- `notification:123e4567-e89b-12d3-a456-426614174000`

This ensures messages are isolated per user and per channel type.

## Message Format

Published messages are JSON-serialized AuditLog entities:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "activity_type": "TASK_COMPLETED",
  "occurred_at": "2026-01-14T10:00:00Z",
  "entity_id": "uuid",
  "entity_type": "task",
  "meta": {
    "action_created_at": "2026-01-14T10:00:00Z"
  }
}
```

## Usage Examples

### Publishing (Automatic)

Publishing happens automatically when AuditLog entities are created through the UnitOfWork:

```python
from lykke.domain.entities import AuditLogEntity
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

async def record_task_completion(user_id: UUID, task_id: UUID):
    audit_log = AuditLogEntity.create_task_completed(
        user_id=user_id,
        task_id=task_id,
        meta={"extra": "data"}
    )

    # The UnitOfWork (configured with PubSub gateway) will automatically
    # broadcast this audit log after successful commit
    async with uow:
        await uow.create(audit_log)
```

### Subscribing and Sending Messages

Subscriptions support both receiving and sending messages, using an async context manager for automatic cleanup:

```python
from lykke.infrastructure.gateways import RedisPubSubGateway

async def monitor_user_activity(user_id: UUID):
    gateway = RedisPubSubGateway()

    # Subscribe to user's auditlog channel (context manager automatically cleans up)
    async with gateway.subscribe_to_user_channel(
        user_id=user_id,
        channel_type="auditlog"
    ) as subscription:
        while True:
            # Wait for messages (with optional timeout)
            message = await subscription.get_message(timeout=30.0)

            if message:
                print(f"Received audit log: {message['activity_type']}")

                # You can also send messages through the subscription
                await subscription.send_message({
                    "type": "acknowledgment",
                    "received_at": datetime.now(UTC).isoformat()
                })
            else:
                # Timeout occurred, no message received
                pass

    # Subscription automatically closed when exiting context
    await gateway.close()
```

## WebSocket Integration (To Implement)

Here's how to integrate this with a WebSocket handler using the context manager pattern:

```python
from fastapi import WebSocket
from lykke.infrastructure.gateways import RedisPubSubGateway

async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    await websocket.accept()

    gateway = RedisPubSubGateway()

    # Use context manager for automatic cleanup
    async with gateway.subscribe_to_user_channel(
        user_id=user_id,
        channel_type="auditlog"
    ) as subscription:
        try:
            while True:
                # Non-blocking check for Redis messages
                redis_message = await subscription.get_message(timeout=0.1)

                if redis_message:
                    # Send the audit log to the WebSocket client
                    await websocket.send_json({
                        "type": "auditlog",
                        "data": redis_message
                    })

                # Check for WebSocket messages from client
                try:
                    client_message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=0.1
                    )

                    # Client can send messages that get broadcast to other subscribers
                    if client_message.get("broadcast"):
                        await subscription.send_message({
                            "type": "client_broadcast",
                            "data": client_message["data"]
                        })

                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await websocket.close()

    # Subscription automatically closed when exiting context
    await gateway.close()
```

### Bidirectional Communication

The subscription supports bidirectional communication - you can both receive and send messages:

```python
async with gateway.subscribe_to_user_channel(user_id, "auditlog") as sub:
    # Receive messages published by other processes
    message = await sub.get_message(timeout=1.0)

    # Send messages to the channel (broadcasts to all subscribers)
    await sub.send_message({"response": "acknowledged"})
```

This is particularly useful for:

- WebSocket handlers that need to relay client messages
- Two-way communication between services
- Broadcasting responses or acknowledgments

## Configuration

The Redis connection is configured via environment variable:

```bash
REDIS_URL=redis://localhost:6379
```

For production, use a proper Redis URL with authentication:

```bash
REDIS_URL=redis://username:password@hostname:6379/0
```

## Testing

### Unit Tests

Unit tests verify the RedisPubSubGateway functionality:

```bash
poetry run pytest tests/unit/gateways/test_redis_pubsub.py -v
```

### Integration Tests

Integration tests verify the full flow with UnitOfWork:

```bash
# Requires test database to be running
poetry run pytest tests/integration/test_auditlog_pubsub.py -v
```

## Delivery Guarantees

### Important Notes

- **Redis Pub/Sub uses at-most-once delivery**: If a subscriber is not connected when a message is published, the message is lost.
- **No persistence**: Messages are not stored in Redis.
- **For guaranteed delivery**: Consider using Redis Streams instead of Pub/Sub.

For the current use case (real-time notifications to active WebSocket connections), this is acceptable. If a client is offline, they won't receive the message, but they can query the database for historical audit logs.

## Performance Considerations

- Redis Pub/Sub is very fast and low-latency
- Each published message is sent to all active subscribers
- The PubSub gateway maintains a single Redis connection
- Failed publications are logged but don't affect the transaction

## Error Handling

- If PubSub publishing fails, it's logged as an error but doesn't rollback the transaction
- This ensures database consistency even if Redis is temporarily unavailable
- Subscribers should handle connection errors and reconnect automatically

## API Reference

### PubSubGateway Methods

#### `publish_to_user_channel(user_id, channel_type, message)`

Publish a message to a user-specific channel.

#### `subscribe_to_user_channel(user_id, channel_type)`

Returns a context manager for subscribing to a user-specific channel.

### PubSubSubscription Methods (Context Manager)

#### `async with subscription:`

Automatically subscribes on enter and cleans up on exit.

#### `get_message(timeout=None)`

Receive the next message from the channel. Returns `None` on timeout.

#### `send_message(message)`

Send a message to the channel (broadcasts to all subscribers).

#### `close()`

Manually close the subscription (not needed when using context manager).

## Future Enhancements

1. **Multiple Channel Types**: Add support for other real-time events (notifications, calendar updates, etc.)
2. **Message Filtering**: Allow subscribers to filter messages by activity type
3. **Redis Streams**: Migrate to Redis Streams for guaranteed delivery and message history
4. **Connection Pooling**: Optimize Redis connection management for high-scale scenarios
5. **Pattern Subscriptions**: Support pattern-based subscriptions (e.g., `auditlog:*` for all users)
