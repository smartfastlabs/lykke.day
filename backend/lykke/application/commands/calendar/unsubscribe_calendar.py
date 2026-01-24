"""Command to unsubscribe a calendar from push notifications."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.domain.entities import CalendarEntity


@dataclass(frozen=True)
class UnsubscribeCalendarCommand(Command):
    """Command to unsubscribe a calendar from push notifications."""

    calendar: CalendarEntity


class UnsubscribeCalendarHandler(
    BaseCommandHandler[UnsubscribeCalendarCommand, CalendarEntity]
):
    """Removes push subscriptions for a calendar."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def handle(self, command: UnsubscribeCalendarCommand) -> CalendarEntity:
        """Remove the existing sync subscription for a calendar."""
        calendar = command.calendar
        async with self.new_uow() as uow:
            if calendar.platform != "google":
                raise NotImplementedError(
                    f"Unsubscribe not implemented for platform {calendar.platform}"
                )

            if not calendar.sync_subscription:
                return calendar

            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)

            await self._google_gateway.unsubscribe_from_calendar(
                calendar=calendar,
                token=token,
                channel_id=calendar.sync_subscription.subscription_id,
                resource_id=calendar.sync_subscription.resource_id,
            )

            calendar.sync_subscription = None
            calendar.sync_subscription_id = None

            return uow.add(calendar)
