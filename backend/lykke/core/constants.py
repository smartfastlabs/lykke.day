"""Application-wide constants.

This module contains magic values and constants used throughout the application
to improve maintainability and avoid hardcoded values.
"""

import datetime

# Time deltas
DEFAULT_LOOK_AHEAD: datetime.timedelta = datetime.timedelta(minutes=30)
"""Default time window for looking ahead at upcoming tasks and events."""

CALENDAR_SYNC_LOOKBACK: datetime.timedelta = datetime.timedelta(minutes=30)
"""Time window to look back when syncing calendar events."""

CALENDAR_DEFAULT_LOOKBACK: datetime.timedelta = datetime.timedelta(days=2)
"""Default time window to look back when syncing calendar events (used when no last_sync_at)."""

OAUTH_STATE_EXPIRY: datetime.timedelta = datetime.timedelta(minutes=10)
"""Expiry time for OAuth state tokens."""

# Time values
DEFAULT_END_OF_DAY_TIME: datetime.time = datetime.time(23, 59)
"""Default time used for tasks without a schedule start time (end of day)."""

# HTTP Status Codes
# These are standard HTTP status codes, but defined here for clarity and consistency
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# Redis keys/channels
DOMAIN_EVENT_BACKLOG_KEY_PREFIX = "domain-events:backlog"
MAX_DOMAIN_EVENT_BACKLOG_SIZE = 10_000
