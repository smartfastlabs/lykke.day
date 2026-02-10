"""Command to create a first-party (Lykke) calendar entry."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.calendar import (
    EnsureLykkeCalendarCommand,
    EnsureLykkeCalendarHandler,
)
from lykke.application.repositories import CalendarEntryRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity


@dataclass(frozen=True)
class CreateCalendarEntryCommand(Command):
    """Command to create a first-party Lykke calendar entry (timed event)."""

    name: str
    starts_at: datetime
    ends_at: datetime
    category: value_objects.EventCategory | None = None


class CreateCalendarEntryHandler(
    BaseCommandHandler[CreateCalendarEntryCommand, CalendarEntryEntity]
):
    """Create a first-party calendar entry on the user's Lykke calendar."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(
        self, command: CreateCalendarEntryCommand
    ) -> CalendarEntryEntity:
        """Create a Lykke calendar entry with the given times."""
        assert self.command_factory is not None
        ensure_handler = cast(
            EnsureLykkeCalendarHandler,
            self.command_factory.create(EnsureLykkeCalendarHandler),
        )
        calendar = await ensure_handler.handle(EnsureLykkeCalendarCommand())

        starts_at = command.starts_at
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=UTC)
        ends_at = command.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=UTC)

        user_timezone = self.user.settings.timezone or "UTC"
        entry = CalendarEntryEntity(
            user_id=self.user.id,
            calendar_id=calendar.id,
            name=command.name,
            platform="lykke",
            platform_id=uuid4().hex,
            status="confirmed",
            frequency=value_objects.TaskFrequency.ONCE,
            starts_at=starts_at,
            ends_at=ends_at,
            category=command.category,
            user_timezone=user_timezone,
        )
        entry.create()

        async with self.new_uow() as uow:
            return uow.add(entry)
