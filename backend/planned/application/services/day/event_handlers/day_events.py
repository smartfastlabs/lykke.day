"""Event handler for day-related domain events."""

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from planned.application.services.event_handler import EventHandler
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain import entities as objects
from planned.domain.events.base import DomainEvent
from planned.domain.events.day_events import (
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
)

if TYPE_CHECKING:
    from ..service import DayService


class DayEventHandler(EventHandler["DayService"]):
    """Handles day-related domain events for DayService.

    Keeps the DayContext's day entity synchronized with day changes.
    """

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        date: datetime.date,
    ) -> None:
        """Initialize the day event handler.

        Args:
            uow_factory: Factory for creating UnitOfWork instances
            user_id: The user ID for database operations
            date: The date this handler is responsible for
        """
        super().__init__()
        self._uow_factory = uow_factory
        self._user_id = user_id
        self._date = date

    @property
    def day_ctx(self) -> objects.DayContext:
        """Get the DayContext from the parent service."""
        return self.service.day_ctx

    @property
    def date(self) -> datetime.date:
        """Get the date this handler is responsible for."""
        return self._date

    @date.setter
    def date(self, value: datetime.date) -> None:
        """Set the date this handler is responsible for."""
        self._date = value

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can handle the given event."""
        if not isinstance(
            event,
            DayScheduledEvent | DayCompletedEvent | DayUnscheduledEvent,
        ):
            return False
        # Only handle events for our date
        return event.date == self._date

    async def handle(self, event: DomainEvent) -> None:
        """Handle a day domain event."""
        if isinstance(event, DayScheduledEvent | DayCompletedEvent):
            await self._handle_status_change(event)
        elif isinstance(event, DayUnscheduledEvent):
            await self._handle_unscheduled(event)

    async def _handle_status_change(
        self,
        event: DayScheduledEvent | DayCompletedEvent,
    ) -> None:
        """Handle day status change by reloading the day.

        Args:
            event: The day status change event
        """
        # Reload the day from database
        uow = self._uow_factory.create(self._user_id)
        async with uow:
            try:
                updated_day = await uow.days.get(event.day_id)
                self.day_ctx.day = updated_day
                logger.debug(f"Updated day {event.day_id} in DayService cache")
            except NotFoundError:
                logger.warning(f"Day {event.day_id} not found after status change")

    async def _handle_unscheduled(self, event: DayUnscheduledEvent) -> None:
        """Handle day unscheduled event.

        Args:
            event: The day unscheduled event
        """
        # Reload the day from database
        uow = self._uow_factory.create(self._user_id)
        async with uow:
            try:
                updated_day = await uow.days.get(event.day_id)
                self.day_ctx.day = updated_day
                logger.debug(f"Updated unscheduled day {event.day_id} in cache")
            except NotFoundError:
                logger.warning(f"Day {event.day_id} not found after unschedule")
