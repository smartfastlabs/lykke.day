"""Taskiq worker configuration."""

from taskiq import InMemoryBroker
from taskiq_redis import ListQueueBroker

from planned.core.config import settings

# Use Redis broker in production, InMemoryBroker for testing
if settings.ENVIRONMENT == "development":
    broker = InMemoryBroker()
else:
    broker = ListQueueBroker(url=settings.REDIS_URL)

# Import tasks after broker is created to register them
# This import must happen after broker definition to avoid circular imports
from planned.presentation.workers import tasks  # noqa: E402, F401

