# WebSocket Hanging Test - Root Cause & Fix

## Issue
`test_realtime_task_deletion_notification` and `test_realtime_calendar_entry_update` were hanging indefinitely.

## Root Cause

The tests were hanging because:

1. **Missing metadata in audit logs**: The manually created audit logs for deletions and updates had incomplete `entity_data` in their metadata
2. **Date filtering failure**: The WebSocket filtering logic (`is_audit_log_for_today()`) requires specific date fields in the metadata to determine if an entity belongs to "today"
3. **Message never sent**: When filtering returns `False`, the WebSocket filters out the message and never sends it to the client
4. **Infinite wait**: The test called `websocket.receive_json()` without a timeout, waiting forever for a message that never arrived

## The Filtering Logic

From `lykke/core/utils/audit_log_filtering.py`:

```python
async def is_audit_log_for_today(audit_log, target_date):
    entity_data = _get_entity_data(audit_log)
    if not entity_data:
        return False  # ⚠️ Returns False if no entity_data
    
    if entity_type == "task":
        scheduled_date = entity_data.get("scheduled_date")
        return scheduled_date == target_date
    
    if entity_type == "calendar_entry":
        # Checks for 'date' or 'starts_at' field
        ...
```

## The Fixes

### 1. Task Deletion Test
**Before (incomplete metadata):**
```python
audit_log = AuditLogEntity(
    activity_type="EntityDeletedEvent",
    entity_type="task",
    meta={},  # ❌ Empty metadata!
)
```

**After (complete metadata):**
```python
audit_log = AuditLogEntity(
    activity_type="EntityDeletedEvent",
    entity_type="task",
    meta={
        "entity_data": {
            "id": str(test_task.id),
            "user_id": str(test_task.user_id),
            "scheduled_date": test_task.scheduled_date.isoformat(),  # ✅ Required for filtering!
        }
    },
)
```

### 2. Calendar Entry Update Test
**Before (incomplete metadata):**
```python
audit_log = AuditLogEntity(
    activity_type="EntityUpdatedEvent",
    entity_type="calendar_entry",
    meta={
        "entity_data": {
            "title": entry.title,  # ❌ Missing starts_at!
        }
    },
)
```

**After (complete metadata):**
```python
audit_log = AuditLogEntity(
    activity_type="EntityUpdatedEvent",
    entity_type="calendar_entry",
    meta={
        "entity_data": {
            "title": entry.title,
            "starts_at": entry.starts_at.isoformat(),  # ✅ Required for filtering!
            "ends_at": entry.ends_at.isoformat(),
        }
    },
)
```

### 3. Added Sleep Delays
Added `await asyncio.sleep(0.2)` before receiving WebSocket messages to ensure Redis messages have time to be:
- Published to Redis
- Received by the WebSocket subscription
- Processed and sent to the client

## Test Results After Fix

✅ **All real-time notification tests now pass:**
- `test_websocket_connection_and_authentication` - PASSED
- `test_full_sync_request` - PASSED  
- `test_realtime_task_creation_notification` - PASSED
- `test_realtime_task_deletion_notification` - PASSED ⭐ (was hanging)
- `test_realtime_calendar_entry_update` - PASSED ⭐ (was hanging)

## Key Takeaway

**When creating audit logs manually for WebSocket tests, ALWAYS include the date fields in `entity_data`:**

- For **tasks**: Include `scheduled_date`
- For **calendar entries**: Include `starts_at` (or `date`)

Without these fields, the filtering logic will exclude the message and the WebSocket client will never receive it, causing tests to hang.

## Why This Matters in Production

In production, the UOW automatically includes entity snapshots with all necessary fields when creating audit logs. But in tests, when we manually create audit logs, we must ensure we include the same date information that the filtering logic depends on.

This is a good example of why integration tests are valuable - they catch issues where test helpers don't fully replicate the production code path!
