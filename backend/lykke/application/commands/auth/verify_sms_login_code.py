"""Command to verify an SMS login code and return the user."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import SmsLoginCodeRepositoryReadWriteProtocol
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.core.exceptions import AuthenticationError
from lykke.core.utils.phone_numbers import digits_only, normalize_phone_number
from lykke.core.utils.sms_code import verify_code
from lykke.domain import value_objects
from lykke.domain.entities import DayTemplateEntity, SmsLoginCodeEntity, UserEntity


@dataclass(frozen=True)
class VerifySmsLoginCodeCommand(Command):
    """Command to verify an SMS login code."""

    phone_number: str
    code: str


MAX_VERIFY_ATTEMPTS = 5


class VerifySmsLoginCodeHandler(
    BaseCommandHandler[VerifySmsLoginCodeCommand, UserEntity]
):
    """Verify SMS code and return the user (creating one if first-time signup)."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user: UserEntity,
        sms_login_code_repo: SmsLoginCodeRepositoryReadWriteProtocol,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user)
        self._sms_login_code_repo = sms_login_code_repo

    async def handle(self, command: VerifySmsLoginCodeCommand) -> UserEntity:
        """Verify code, get or create user, return user entity."""
        normalized = normalize_phone_number(command.phone_number)
        if not normalized:
            raise AuthenticationError("Invalid phone number")

        code_entity = await self._sms_login_code_repo.search_one_or_none(
            value_objects.SmsLoginCodeQuery(phone_number=normalized, consumed=False)
        )
        if code_entity is None:
            raise AuthenticationError("Invalid or expired code")

        if code_entity.attempt_count >= MAX_VERIFY_ATTEMPTS:
            raise AuthenticationError("Too many attempts")

        if code_entity.expires_at < datetime.now(UTC):
            raise AuthenticationError("Invalid or expired code")

        if not verify_code(command.code, code_entity.code_hash):
            await self._sms_login_code_repo.mark_consumed_and_increment_attempts(
                code_entity.id, consumed=False
            )
            raise AuthenticationError("Invalid or expired code")

        await self._sms_login_code_repo.mark_consumed_and_increment_attempts(
            code_entity.id, consumed=True
        )

        user = await self.user_ro_repo.search_one_or_none(
            value_objects.UserQuery(phone_number=normalized)
        )
        is_new_user = user is None
        if user is None:
            user = self._build_user(normalized)

        async with self._uow_factory.create(user) as uow:
            if is_new_user:
                await self._create_user(uow, user)

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

    async def _create_user(
        self, uow: UnitOfWorkProtocol, user: UserEntity
    ) -> None:
        """Create a new user with default day templates."""
        await uow.create(user)

        default_templates = [
            DayTemplateEntity(user_id=user.id, slug="default", icon=None),
            DayTemplateEntity(user_id=user.id, slug="workday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekend", icon=None),
        ]
        for template in default_templates:
            await uow.create(template)

        return None
