"""Command to request an SMS login code."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from lykke.application.commands.base import Command
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.gateways import SMSProviderProtocol
from lykke.core.utils.phone_numbers import normalize_phone_number
from lykke.core.utils.sms_code import generate_code, hash_code
from lykke.domain.entities import SmsLoginCodeEntity


@dataclass(frozen=True)
class RequestSmsLoginCodeCommand(Command):
    """Command to request an SMS login code for a phone number."""

    phone_number: str


CODE_EXPIRY_MINUTES = 10
SMS_MESSAGE_TEMPLATE = "Your lykke.day login code is: {code}"


class RequestSmsLoginCodeHandler:
    """Request an SMS login code and send it via SMS."""

    def __init__(
        self,
        identity_access: UnauthenticatedIdentityAccessProtocol,
        sms_gateway: SMSProviderProtocol,
    ) -> None:
        self._identity_access = identity_access
        self._sms_gateway = sms_gateway

    async def handle(self, command: RequestSmsLoginCodeCommand) -> None:
        """Generate code, store hashed, and send SMS. Always returns success (no info leak)."""
        normalized = normalize_phone_number(command.phone_number)
        if not normalized:
            return

        code = generate_code(6)
        code_hash = hash_code(code)
        expires_at = datetime.now(UTC) + timedelta(minutes=CODE_EXPIRY_MINUTES)

        entity = SmsLoginCodeEntity(
            phone_number=normalized,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        await self._identity_access.create_sms_login_code(entity)

        message = SMS_MESSAGE_TEMPLATE.format(code=code)
        await self._sms_gateway.send_message(normalized, message)
