"""E2E tests for brain dump processing enqueueing."""

from uuid import UUID

import pytest

from lykke.core.utils.dates import get_current_date
from lykke.presentation.workers import tasks as worker_tasks
from tests.e2e.conftest import schedule_day_for_user


class _DummyWorker:
    __name__ = "dummy_worker"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def kiq(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


@pytest.mark.asyncio
async def test_add_brain_dump_enqueues_processing(authenticated_client) -> None:
    client, user = await authenticated_client()
    today = get_current_date(user.settings.timezone)
    await schedule_day_for_user(user.id, today)

    dummy_worker = _DummyWorker()
    worker_tasks.set_worker_override(
        worker_tasks.process_brain_dump_item_task,
        dummy_worker,
    )
    try:
        response = client.post(
            "/me/today/brain-dump",
            params={"text": "Need to follow up on the proposal"},
        )

        assert response.status_code == 200
        data = response.json()
        item_id = UUID(data["id"])

        assert len(dummy_worker.calls) == 1
        call = dummy_worker.calls[0]
        assert call["user_id"] == user.id
        assert call["day_date"] == today.isoformat()
        assert call["item_id"] == item_id
    finally:
        worker_tasks.clear_worker_overrides()
