"""Command to create a lead-only user from early access form."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


@dataclass(kw_only=True)
class CreateLeadUserData(value_objects.BaseRequestObject):
    """Normalized contact data for lead capture."""

    email: str | None = None
    phone_number: str | None = None


class CreateLeadUserHandler(BaseCommandHandler):
    """Create a lead user with status NEW_LEAD."""

    async def run(self, data: CreateLeadUserData) -> None:
        """Create a lead if unique by email/phone."""
        async with self.new_uow() as uow:
            if data.email:
                existing = await uow.user_ro_repo.get_by_email(data.email)
                if existing:
                    return

            if data.phone_number:
                existing = await uow.user_ro_repo.get_by_phone(data.phone_number)
                if existing:
                    return

            lead = UserEntity(
                email=data.email,
                phone_number=data.phone_number,
                hashed_password="!",
                is_active=False,
                is_superuser=False,
                is_verified=False,
                status=value_objects.UserStatus.NEW_LEAD,
            )

            await uow.create(lead)

