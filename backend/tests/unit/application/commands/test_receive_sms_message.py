"""Unit tests for ReceiveSmsMessageHandler."""

from uuid import uuid4

import pytest

from lykke.application.commands.message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from lykke.domain import value_objects
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_receive_sms_sets_message_type_to_inbound() -> None:
    user_id = uuid4()

    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)

    handler = ReceiveSmsMessageHandler(ro_repos, uow_factory, user_id)

    result = await handler.handle(
        ReceiveSmsMessageCommand(
            from_number="+15551234567",
            to_number="+15557654321",
            body="hello",
            payload={"From": "+15551234567", "Body": "hello"},
        )
    )

    assert result.type == value_objects.MessageType.SMS_INBOUND
    assert uow.added
    assert uow.added[0].type == value_objects.MessageType.SMS_INBOUND
