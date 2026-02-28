"""Unit tests for ReceiveSmsMessageHandler."""

from uuid import uuid4

import pytest

from lykke.application.commands.message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from lykke.application.worker_schedule import (
    reset_current_workers_to_schedule,
    set_current_workers_to_schedule,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _WorkersToSchedule:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def schedule_process_brain_dump_item(
        self, *, user_id: object, day_date: object, item_id: object
    ) -> None:
        _ = (user_id, day_date, item_id)

    def schedule_process_inbound_sms_message(
        self, *, user_id: object, message_id: object
    ) -> None:
        self.calls.append(
            {
                "user_id": user_id,
                "message_id": message_id,
            }
        )

    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_receive_sms_sets_message_type_to_inbound() -> None:
    user_id = uuid4()

    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)

    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = ReceiveSmsMessageHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )

    workers_to_schedule = _WorkersToSchedule()
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
        result = await handler.handle(
            ReceiveSmsMessageCommand(
                from_number="+15551234567",
                to_number="+15557654321",
                body="hello",
                payload={"From": "+15551234567", "Body": "hello"},
            )
        )
    finally:
        reset_current_workers_to_schedule(token)

    assert result.type == value_objects.MessageType.SMS_INBOUND
    assert uow.added
    assert uow.added[0].type == value_objects.MessageType.SMS_INBOUND
    assert uow.added[0].triggered_by == "sms_inbound"
    assert len(workers_to_schedule.calls) == 1
    kwargs = workers_to_schedule.calls[0]
    assert kwargs["user_id"] == user_id
    assert kwargs["message_id"] == result.id
