from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from loguru import logger

from lykke.application.commands.message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.utils.phone_numbers import normalize_phone_number
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
)
from lykke.presentation.webhook_relay import webhook_relay_manager

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
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol,
        Depends(lambda: UnauthenticatedIdentityAccess()),
    ],
) -> Response:
    """Webhook endpoint for inbound Twilio SMS messages."""
    relay_response = await webhook_relay_manager.proxy_request(request)
    if relay_response is not None:
        return relay_response

    form = await request.form()
    payload = _normalize_twilio_payload(dict(form))

    from_number = payload.get("From")
    to_number = payload.get("To")
    body = payload.get("Body")

    if not from_number or body is None:
        logger.warning("Twilio SMS webhook missing From/Body")
        return Response(status_code=200)

    from_number = normalize_phone_number(from_number)
    to_number = normalize_phone_number(to_number) if to_number else None

    user = await identity_access.get_user_by_phone_number(from_number)
    if user is None:
        logger.warning("No user found for inbound SMS from {}", from_number)
        return Response(status_code=200)

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    handler = factory.create(ReceiveSmsMessageHandler)
    await handler.handle(
        ReceiveSmsMessageCommand(
            from_number=from_number,
            to_number=to_number,
            body=body,
            payload=payload,
        )
    )

    return Response(status_code=200)
