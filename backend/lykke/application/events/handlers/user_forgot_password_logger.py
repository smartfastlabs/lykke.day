"""Event handler that logs forgot password requests."""

from typing import ClassVar

from loguru import logger

from lykke.domain.events.base import DomainEvent
from lykke.domain.events.user_events import UserForgotPasswordEvent

from .base import DomainEventHandler


class UserForgotPasswordLoggerHandler(DomainEventHandler):
    """Log the details required to compose a reset password email."""

    handles: ClassVar[list[type[DomainEvent]]] = [UserForgotPasswordEvent]

    async def handle(self, event: DomainEvent) -> None:
        """Log the information needed for composing a reset email."""
        if not isinstance(event, UserForgotPasswordEvent):
            return

        reset_path = f"/reset-password?token={event.reset_token}"
        logger.info(
            "Password reset requested for {email} (user_id={user_id}) "
            "reset_path={reset_path} origin={origin} user_agent={user_agent}",
            email=event.email,
            user_id=event.user_id,
            reset_path=reset_path,
            origin=event.request_origin,
            user_agent=event.user_agent,
        )
