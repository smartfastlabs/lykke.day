"""SMS-based auth endpoints: request and verify login codes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from starlette.responses import Response

from lykke.application.commands.auth import (
    RequestSmsLoginCodeCommand,
    RequestSmsLoginCodeHandler,
    VerifySmsLoginCodeCommand,
    VerifySmsLoginCodeHandler,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import UnitOfWorkFactory
from lykke.core.exceptions import AuthenticationError
from lykke.infrastructure.auth import auth_backend, get_jwt_strategy
from lykke.infrastructure.gateways import TwilioGateway
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.api.schemas.auth_sms import (
    RequestSmsCodeSchema,
    VerifySmsCodeSchema,
)

from .dependencies.services import get_unit_of_work_factory

router = APIRouter()


def get_identity_access() -> UnauthenticatedIdentityAccessProtocol:
    """Identity access for unauthenticated flows (override in tests)."""
    return UnauthenticatedIdentityAccess()


def get_sms_gateway() -> SMSProviderProtocol:
    """SMS gateway - override in tests with StubSMSGateway."""
    return TwilioGateway()


def _provider_request_sms(
    identity_access: UnauthenticatedIdentityAccessProtocol,
    _uow_factory: UnitOfWorkFactory,
    sms_gateway: SMSProviderProtocol,
) -> RequestSmsLoginCodeHandler:
    return RequestSmsLoginCodeHandler(
        identity_access=identity_access,
        sms_gateway=sms_gateway,
    )


def _provider_verify_sms(
    identity_access: UnauthenticatedIdentityAccessProtocol,
    uow_factory: UnitOfWorkFactory,
    _sms_gateway: SMSProviderProtocol,
) -> VerifySmsLoginCodeHandler:
    return VerifySmsLoginCodeHandler(
        identity_access=identity_access,
        uow_factory=uow_factory,
    )


_UNAUTH_AUTH_HANDLER_PROVIDERS: dict[type, Any] = {
    RequestSmsLoginCodeHandler: _provider_request_sms,
    VerifySmsLoginCodeHandler: _provider_verify_sms,
}


def create_unauth_auth_handler(handler_class: type) -> Any:
    """Dependency factory that returns a ready-to-use unauthenticated auth handler.

    Usage: handler: Annotated[MyHandler, Depends(create_unauth_auth_handler(MyHandler))]
    """

    def _dependency(
        identity_access: Annotated[
            UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
        ],
        uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
        sms_gateway: Annotated[SMSProviderProtocol, Depends(get_sms_gateway)],
    ) -> Any:
        provider = _UNAUTH_AUTH_HANDLER_PROVIDERS[handler_class]
        return provider(identity_access, uow_factory, sms_gateway)

    return _dependency


@router.post("/request", status_code=200)
async def request_sms_code(
    data: RequestSmsCodeSchema,
    handler: Annotated[
        RequestSmsLoginCodeHandler, Depends(create_unauth_auth_handler(RequestSmsLoginCodeHandler))
    ],
) -> dict[str, str]:
    """Request an SMS login code. Always returns success (no info leak)."""
    await handler.handle(RequestSmsLoginCodeCommand(phone_number=data.phone_number))
    return {"status": "ok"}


@router.post("/verify", status_code=204)
async def verify_sms_code(
    data: VerifySmsCodeSchema,
    handler: Annotated[
        VerifySmsLoginCodeHandler, Depends(create_unauth_auth_handler(VerifySmsLoginCodeHandler))
    ],
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
) -> Response:
    """Verify SMS code and set auth cookie. Returns 204 on success."""
    user_entity = await handler.handle(
        VerifySmsLoginCodeCommand(
            phone_number=data.phone_number,
            code=data.code,
        )
    )

    user_db = await identity_access.load_user_db_for_login(user_entity.id)
    if user_db is None:
        raise AuthenticationError("User not found")

    jwt_strategy = get_jwt_strategy()
    return await auth_backend.login(jwt_strategy, user_db)  # type: ignore[arg-type]
