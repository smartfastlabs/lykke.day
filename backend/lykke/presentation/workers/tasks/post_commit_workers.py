"""Post-commit workers-to-schedule implementation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from loguru import logger

from lykke.application.worker_schedule import WorkersToScheduleProtocol

from .registry import WorkerRegistry


@dataclass(frozen=True)
class _ProcessBrainDumpItemJob:
    user_id: UUID
    day_date: str
    item_id: UUID


@dataclass(frozen=True)
class _ProcessInboundSmsJob:
    user_id: UUID
    message_id: UUID


class WorkersToSchedule(WorkersToScheduleProtocol):
    """UOW-scoped collection of workers to schedule after commit."""

    def __init__(self, worker_registry: WorkerRegistry) -> None:
        self._worker_registry = worker_registry
        self._pending_brain_dump_items: list[_ProcessBrainDumpItemJob] = []
        self._pending_inbound_sms: list[_ProcessInboundSmsJob] = []

    def schedule_process_brain_dump_item(
        self, *, user_id: UUID, day_date: str, item_id: UUID
    ) -> None:
        """Add a brain-dump job to be sent to the broker after commit."""
        self._pending_brain_dump_items.append(
            _ProcessBrainDumpItemJob(
                user_id=user_id,
                day_date=day_date,
                item_id=item_id,
            )
        )

    def schedule_process_inbound_sms_message(
        self, *, user_id: UUID, message_id: UUID
    ) -> None:
        """Add an inbound-SMS job to be sent to the broker after commit."""
        self._pending_inbound_sms.append(
            _ProcessInboundSmsJob(user_id=user_id, message_id=message_id)
        )

    async def flush(self) -> None:
        """Send all scheduled workers to the broker."""
        from .brain_dump import process_brain_dump_item_task
        from .inbound_sms import process_inbound_sms_message_task

        for brain_dump_job in self._pending_brain_dump_items:
            try:
                resolved_worker = self._worker_registry.get_worker(
                    process_brain_dump_item_task
                )
                await resolved_worker.kiq(
                    user_id=brain_dump_job.user_id,
                    day_date=brain_dump_job.day_date,
                    item_id=brain_dump_job.item_id,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    f"Failed to schedule worker {getattr(resolved_worker, 'task_name', resolved_worker)}: {exc}",
                )

        for inbound_sms_job in self._pending_inbound_sms:
            try:
                resolved_worker = self._worker_registry.get_worker(
                    process_inbound_sms_message_task
                )
                await resolved_worker.kiq(
                    user_id=inbound_sms_job.user_id,
                    message_id=inbound_sms_job.message_id,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    f"Failed to schedule worker {getattr(resolved_worker, 'task_name', resolved_worker)}: {exc}",
                )

        self._pending_brain_dump_items.clear()
        self._pending_inbound_sms.clear()
