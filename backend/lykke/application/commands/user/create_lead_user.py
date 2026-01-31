"""Command to create a lead-only user from early access form."""

from dataclasses import dataclass
from uuid import uuid4

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.utils.phone_numbers import digits_only, normalize_phone_number
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


@dataclass(frozen=True)
class CreateLeadUserCommand(Command):
    """Command to create a lead user."""

    email: str | None = None
    phone_number: str | None = None


class CreateLeadUserHandler(BaseCommandHandler[CreateLeadUserCommand, None]):
    """Create a lead user with status NEW_LEAD."""

    async def handle(self, command: CreateLeadUserCommand) -> None:
        """Create a lead if unique by phone/email."""
        async with self.new_uow() as uow:
            normalized_email = command.email.strip().lower() if command.email else None
            normalized_phone = (
                normalize_phone_number(command.phone_number)
                if command.phone_number
                else None
            )

            if normalized_email:
                existing_by_email = await uow.user_ro_repo.search_one_or_none(
                    value_objects.UserQuery(email=normalized_email)
                )
                if existing_by_email:
                    return

            if normalized_phone:
                existing_by_phone = await uow.user_ro_repo.search_one_or_none(
                    value_objects.UserQuery(phone_number=normalized_phone)
                )
                if existing_by_phone:
                    return

            # Users require phone_number; when capturing email-only leads, use placeholder
            if not normalized_phone:
                normalized_phone = (
                    f"+1{digits_only(normalized_email or '') or uuid4().hex[:10]}"
                )

            # Users require an email in storage; when capturing phone-only leads,
            # generate a stable placeholder email under a reserved domain.
            if normalized_email:
                email = normalized_email
            else:
                digits = digits_only(normalized_phone or "")
                token = digits if digits else uuid4().hex
                email = f"lead+{token}@leads.lykke.day"

            lead = UserEntity(
                email=email,
                phone_number=normalized_phone,
                hashed_password="!",
                is_active=False,
                is_superuser=False,
                is_verified=False,
                status=value_objects.UserStatus.NEW_LEAD,
            )

            await uow.create(lead)
