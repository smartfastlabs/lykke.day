"""SMS-based auth endpoints: request and verify login codes."""

from typing import Annotated, cast

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.responses import Response

from lykke.application.commands.auth import (
    RequestSmsLoginCodeCommand,
    RequestSmsLoginCodeHandler,
    VerifySmsLoginCodeCommand,
    VerifySmsLoginCodeHandler,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.repositories import SmsLoginCodeRepositoryReadWriteProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.exceptions import AuthenticationError
from lykke.infrastructure.auth import auth_backend, get_jwt_strategy
from lykke.infrastructure.database.tables import User
from lykke.infrastructure.database.utils import get_engine
from lykke.infrastructure.gateways import TwilioGateway
from lykke.infrastructure.repositories import SmsLoginCodeRepository
from lykke.presentation.api.schemas.auth_sms import (
    RequestSmsCodeSchema,
    VerifySmsCodeSchema,
)

from .dependencies.services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)

router = APIRouter()


def _get_sms_login_code_repo() -> SmsLoginCodeRepository:
    return SmsLoginCodeRepository()


def get_sms_gateway() -> SMSProviderProtocol:
    """SMS gateway - override in tests with StubSMSGateway."""
    return TwilioGateway()


def _get_request_handler(
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    sms_gateway: Annotated[SMSProviderProtocol, Depends(get_sms_gateway)],
) -> RequestSmsLoginCodeHandler:
    from uuid import uuid4

    sms_repo = _get_sms_login_code_repo()
    return RequestSmsLoginCodeHandler(
        sms_login_code_repo=cast("SmsLoginCodeRepositoryReadWriteProtocol", sms_repo),
        sms_gateway=sms_gateway,
    )


def _get_verify_handler(
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> VerifySmsLoginCodeHandler:
    from uuid import uuid4

    ro_repos = ro_repo_factory.create(uuid4())
    sms_repo = _get_sms_login_code_repo()
    return VerifySmsLoginCodeHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=uuid4(),
        sms_login_code_repo=cast("SmsLoginCodeRepositoryReadWriteProtocol", sms_repo),
    )


@router.post("/request", status_code=200)
async def request_sms_code(
    data: RequestSmsCodeSchema,
    handler: Annotated[RequestSmsLoginCodeHandler, Depends(_get_request_handler)],
) -> dict[str, str]:
    """Request an SMS login code. Always returns success (no info leak)."""
    await handler.handle(RequestSmsLoginCodeCommand(phone_number=data.phone_number))
    return {"status": "ok"}


@router.post("/verify", status_code=204)
async def verify_sms_code(
    data: VerifySmsCodeSchema,
    handler: Annotated[VerifySmsLoginCodeHandler, Depends(_get_verify_handler)],
) -> Response:
    """Verify SMS code and set auth cookie. Returns 204 on success."""
    user_entity = await handler.handle(
        VerifySmsLoginCodeCommand(
            phone_number=data.phone_number,
            code=data.code,
        )
    )

    # Fetch SQLAlchemy User for auth backend
    engine = get_engine()
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        stmt = select(User).where(User.id == user_entity.id)  # type: ignore[arg-type]
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("User not found")

        jwt_strategy = get_jwt_strategy()
        return await auth_backend.login(jwt_strategy, user)
