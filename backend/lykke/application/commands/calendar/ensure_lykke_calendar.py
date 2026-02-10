"""Command to ensure the user's first-party Lykke calendar exists."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import CalendarRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


@dataclass(frozen=True)
class EnsureLykkeCalendarCommand(Command):
    """Command to ensure the user has a Lykke (first-party) calendar. Creates it if missing."""


class EnsureLykkeCalendarHandler(
    BaseCommandHandler[EnsureLykkeCalendarCommand, CalendarEntity]
):
    """Ensures the user's Lykke calendar exists, creating it lazily if not."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(self, command: EnsureLykkeCalendarCommand) -> CalendarEntity:
        """Ensure Lykke calendar exists; create if missing."""
        platform_id = f"lykke:{self.user.id}"
        existing = await self.calendar_ro_repo.search_one_or_none(
            value_objects.CalendarQuery(platform_id=platform_id)
        )
        if existing is not None:
            return existing

        async with self.new_uow() as uow:
            calendar = CalendarEntity(
                user_id=self.user.id,
                name="Lykke Calendar",
                platform="lykke",
                platform_id=platform_id,
                auth_token_id=None,
            )
            calendar.create()
            return uow.add(calendar)
