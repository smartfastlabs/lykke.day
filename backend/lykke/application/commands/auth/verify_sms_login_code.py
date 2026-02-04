"""Command to verify an SMS login code and return the user."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from lykke.application.commands.base import Command
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import UnitOfWorkFactory
from lykke.core.exceptions import AuthenticationError
from lykke.core.utils.phone_numbers import digits_only, normalize_phone_number
from lykke.core.utils.sms_code import verify_code
from lykke.domain import value_objects
from lykke.domain.entities import DayTemplateEntity, UserEntity


@dataclass(frozen=True)
class VerifySmsLoginCodeCommand(Command):
    """Command to verify an SMS login code."""

    phone_number: str
    code: str


MAX_VERIFY_ATTEMPTS = 5


class VerifySmsLoginCodeHandler:
    """Verify SMS code and return the user (creating one if first-time signup)."""

    def __init__(
        self,
        *,
        identity_access: UnauthenticatedIdentityAccessProtocol,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self._identity_access = identity_access
        self._uow_factory = uow_factory

    async def handle(self, command: VerifySmsLoginCodeCommand) -> UserEntity:
        """Verify code, get or create user, return user entity."""
        normalized = normalize_phone_number(command.phone_number)
        if not normalized:
            raise AuthenticationError("Invalid phone number")

        code_entity = await self._identity_access.get_latest_unconsumed_sms_login_code(
            normalized
        )
        if code_entity is None:
            raise AuthenticationError("Invalid or expired code")

        if code_entity.attempt_count >= MAX_VERIFY_ATTEMPTS:
            raise AuthenticationError("Too many attempts")

        if code_entity.expires_at < datetime.now(UTC):
            raise AuthenticationError("Invalid or expired code")

        valid = verify_code(command.code, code_entity.code_hash)
        code_entity.record_verification_attempt(consumed=valid)
        await self._identity_access.persist_sms_login_code_attempt(code_entity)

        if not valid:
            raise AuthenticationError("Invalid or expired code")

        user = await self._identity_access.get_user_by_phone_number(normalized)
        is_new_user = user is None
        if user is None:
            user = await self._identity_access.create_user(self._build_user(normalized))

        if is_new_user:
            await self._create_default_templates(user)

        return user

    def _build_user(self, phone_number: str) -> UserEntity:
        """Build a new user entity for SMS signup."""
        digits = digits_only(phone_number)
        token = digits if digits else uuid4().hex
        email = f"sms+{token}@sms.lykke.day"
        return UserEntity(
            email=email,
            phone_number=phone_number,
            hashed_password="!",
            is_active=True,
            is_superuser=False,
            is_verified=True,
            status=value_objects.UserStatus.ACTIVE,
        )

    async def _create_default_templates(self, user: UserEntity) -> None:
        """Create default day templates for a newly created user (user-scoped)."""
        default_templates = [
            DayTemplateEntity(user_id=user.id, slug="default", icon=None),
            DayTemplateEntity(user_id=user.id, slug="workday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekend", icon=None),
        ]
        async with self._uow_factory.create(user) as uow:
            for template in default_templates:
                await uow.create(template)

        return None
