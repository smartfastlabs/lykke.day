"""Command to create a lead-only user from early access form."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


@dataclass(frozen=True)
class CreateLeadUserCommand(Command):
    """Command to create a lead user."""

    email: str


class CreateLeadUserHandler(BaseCommandHandler[CreateLeadUserCommand, None]):
    """Create a lead user with status NEW_LEAD."""

    async def handle(self, command: CreateLeadUserCommand) -> None:
        """Create a lead if unique by email."""
        async with self.new_uow() as uow:
            existing = await uow.user_ro_repo.search_one_or_none(
                value_objects.UserQuery(email=command.email)
            )
            if existing:
                return

            lead = UserEntity(
                email=command.email,
                hashed_password="!",
                is_active=False,
                is_superuser=False,
                is_verified=False,
                status=value_objects.UserStatus.NEW_LEAD,
            )

            await uow.create(lead)

