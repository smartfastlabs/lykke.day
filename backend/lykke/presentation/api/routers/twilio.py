from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response
from loguru import logger

from lykke.application.commands.message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from lykke.application.queries.user import GetUserByPhoneHandler, GetUserByPhoneQuery
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)

router = APIRouter()


def _normalize_twilio_payload(
    payload: dict[str, Any],
) -> dict[str, str]:
    """Coerce Twilio payload values into JSON-serializable strings."""
    return {key: "" if value is None else str(value) for key, value in payload.items()}


@router.post("/webhook/sms")
async def twilio_sms_webhook(
    request: Request,
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> Response:
    """Webhook endpoint for inbound Twilio SMS messages."""
    form = await request.form()
    payload = _normalize_twilio_payload(dict(form))

    from_number = payload.get("From")
    to_number = payload.get("To")
    body = payload.get("Body")

    if not from_number or body is None:
        logger.warning("Twilio SMS webhook missing From/Body")
        return Response(status_code=200)

    query_factory = QueryHandlerFactory(
        user_id=uuid4(), ro_repo_factory=ro_repo_factory
    )
    user_handler = query_factory.create(GetUserByPhoneHandler)
    user = await user_handler.handle(GetUserByPhoneQuery(phone_number=from_number))
    if user is None:
        logger.warning("No user found for inbound SMS from {}", from_number)
        return Response(status_code=200)

    conversation_id = user.sms_conversation_id or user.default_conversation_id
    if conversation_id is None:
        logger.warning("User {} has no SMS conversation configured", user.id)
        return Response(status_code=200)

    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    handler = factory.create(ReceiveSmsMessageHandler)
    await handler.handle(
        ReceiveSmsMessageCommand(
            conversation_id=conversation_id,
            from_number=from_number,
            to_number=to_number,
            body=body,
            payload=payload,
        )
    )

    return Response(status_code=200)
