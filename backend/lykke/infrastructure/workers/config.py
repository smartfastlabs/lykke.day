"""Taskiq worker configuration."""

from lykke.core.config import settings
from taskiq_redis import ListQueueBroker

broker = ListQueueBroker(url=settings.REDIS_URL)

# Import tasks after broker is created to register them
# This import must happen after broker definition to avoid circular imports
from lykke.presentation.workers import tasks  # noqa: E402
