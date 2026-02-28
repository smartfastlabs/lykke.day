"""Worker process bootstrap for task registration."""
# pylint: disable=unused-import

from lykke.infrastructure.workers.config import broker

# Import tasks so Taskiq registers all @broker.task definitions on startup.
from lykke.presentation.workers import tasks  # noqa: F401,E402

