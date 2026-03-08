"""Command to create a user-authored check-in."""

from dataclasses import dataclass
from datetime import UTC, datetime

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity


@dataclass(frozen=True)
class CreateUserCheckInCommand(Command):
    """Command to create a user check-in (source=user)."""

    text: str | None = None
    scores: dict[str, float | int] | None = None
    checkin_at: datetime | None = None


class CreateUserCheckInHandler(
    BaseCommandHandler[CreateUserCheckInCommand, UserCheckInEntity]
):
    """Creates a user-authored check-in."""

    async def handle(self, command: CreateUserCheckInCommand) -> UserCheckInEntity:
        """Create a check-in with source=user."""
        checkin_at = command.checkin_at if command.checkin_at is not None else datetime.now(UTC)
        scores = command.scores if command.scores is not None else {}
        async with self.new_uow() as uow:
            entity = UserCheckInEntity(
                user_id=self.user.id,
                source=value_objects.UserCheckInSource.USER,
                source_name=None,
                source_metadata={},
                checkin_at=checkin_at,
                text=command.text,
                scores=scores,
            )
            entity.create()
            created = await uow.create(entity)
            return created
