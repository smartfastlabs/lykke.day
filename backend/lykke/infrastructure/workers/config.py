"""Taskiq worker configuration."""

from taskiq_redis import ListQueueBroker

from lykke.core.config import settings
from lykke.core.observability import init_sentry_taskiq

init_sentry_taskiq()

broker = ListQueueBroker(url=settings.REDIS_URL)
