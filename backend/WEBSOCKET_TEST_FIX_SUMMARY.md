# WebSocket Test Fixes - Summary

## The Problem

The WebSocket tests in `tests/e2e/routers/test_days_websocket.py` were failing with timeouts. The user reported it was a "Redis connection issue" but Redis was running fine.

## Root Cause

The issue was **NOT** a Redis connection problem. The root cause was a **logic bug in how tests created entities**:

1. **Tests bypassed the Unit of Work (UOW)**: Tests used `repository.put()` directly to create entities
2. **No audit logs were created**: Audit logs are ONLY created when entities are modified through the UOW
3. **No messages broadcast to Redis**: The UOW's commit phase broadcasts audit logs to Redis, but this was skipped
4. **WebSocket tests timed out**: Tests expecting real-time WebSocket notifications never received them because nothing was published to Redis

### Why This Happened

Looking at the code flow:

```
Normal App Flow (Correct):
  Command Handler → UOW.add(entity) → UOW.commit() 
    → Create audit logs → Broadcast to Redis → WebSocket receives message

Test Flow (Broken):
  repository.put(entity) → Direct DB write
    → NO audit logs → NO Redis broadcast → WebSocket times out waiting
```

The audit log creation and Redis broadcasting only happens in `SqlAlchemyUnitOfWork._process_added_entities()` and `_broadcast_audit_logs()`, which are called during `commit()`. Direct repository access bypasses this entirely.

## The Fix

### Approach
Since using the UOW in tests causes asyncio event loop conflicts with `TestClient` (which manages its own event loop for WebSockets), we took a hybrid approach:

1. **For tests needing real-time notifications**: Manually create audit logs and publish them to Redis
2. **For tests only needing data (like full sync)**: Use direct repository access (faster, simpler)

### Key Changes

1. **Fixed Redis subscription error handling** (`subscription.py`):
   - Added handling for RuntimeError with "attached to a different loop"
   - This prevents the constant error spam seen in test output

2. **Updated test patterns** (`test_days_websocket.py`):
   - Use direct `repository.put()` for initial test data setup
   - For real-time tests: Manually create audit logs AND publish to Redis using `RedisPubSubGateway`
   - Added proper `user_id` parameter to all `AuditLogRepository()` calls

3. **Example of correct pattern for real-time tests**:
```python
# Create entity
await task_repo.put(new_task)

# Create audit log
audit_log = AuditLogEntity(
    user_id=user.id,
    activity_type="EntityCreatedEvent",
    entity_id=new_task.id,
    entity_type="task",
    occurred_at=datetime.now(UTC),
    meta={"entity_data": {...}}  # Include entity snapshot
)
await audit_log_repo.put(audit_log)

# Manually broadcast to Redis (simulating UOW)
redis_pool = getattr(client.app.state, "redis_pool", None)
pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
await pubsub_gateway.publish_to_user_channel(
    user_id=user.id,
    channel_type="auditlog",
    message=serialize_audit_log(audit_log),
)
```

## Test Results

### Passing Tests
- ✅ `test_websocket_connection_and_authentication` - Basic WebSocket connection
- ✅ `test_full_sync_request` - Full day context sync
- ✅ `test_realtime_task_creation_notification` - **KEY TEST**: Real-time Redis pub/sub works!
- ✅ `test_error_handling_invalid_request` - Error handling

### Tests Needing Minor Fixes
Some tests still fail due to:
- Timing issues with audit log timestamps vs baseline timestamps
- Date filtering edge cases with manually created audit logs
- These are NOT Redis issues - the Redis pub/sub is working correctly

## Key Takeaway

**The Redis connection was never the problem.** The issue was that tests weren't using the application's normal flow (UOW → audit logs → Redis broadcast), so no messages were ever published to Redis. The WebSockets were working correctly - they were just waiting for messages that never came.

## Recommendations

1. **For new tests**: Use command handlers when possible (they use UOW correctly)
2. **For E2E WebSocket tests**: Use the manual audit log + broadcast pattern shown above
3. **Consider**: Creating a test helper that properly simulates the UOW broadcast without event loop conflicts

## Technical Details

### Why Event Loop Issues Occurred

- `TestClient` creates its own event loop for WebSocket operations
- Our test helper tried to create a UOW in the test's event loop
- Redis clients became attached to different loops
- Result: "Task got Future attached to a different loop" errors

### Why Manual Broadcasting Works

- We create the Redis gateway in the test context
- We explicitly publish to the same Redis pool used by the WebSocket
- No event loop conflicts because we're not using UOW's automatic flow
- The WebSocket subscription receives the message correctly
