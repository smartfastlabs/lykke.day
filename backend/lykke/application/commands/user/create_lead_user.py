"""Command to create a lead-only user from early access form."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


@dataclass(kw_only=True)
class CreateLeadUserData(value_objects.BaseRequestObject):
    """Normalized email for lead capture."""

    email: str


class CreateLeadUserHandler(BaseCommandHandler):
    """Create a lead user with status NEW_LEAD."""

    async def run(self, data: CreateLeadUserData) -> None:
        """Create a lead if unique by email."""
        async with self.new_uow() as uow:
            existing = await uow.user_ro_repo.search_one_or_none(
                value_objects.UserQuery(email=data.email)
            )
            if existing:
                return

            lead = UserEntity(
                email=data.email,
                hashed_password="!",
                is_active=False,
                is_superuser=False,
                is_verified=False,
                status=value_objects.UserStatus.NEW_LEAD,
            )

            await uow.create(lead)

