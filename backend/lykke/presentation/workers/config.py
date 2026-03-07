"""Worker broker entrypoint.

Exposes the broker for the taskiq worker CLI. Tasks are imported separately
via the CLI modules argument so that is_worker_process is set on the broker
before any task registration occurs (Taskiq requirement).
"""

from lykke.infrastructure.workers.config import broker

__all__ = ["broker"]

