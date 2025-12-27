"""Protocol for MessageRepository."""

import datetime
from typing import Protocol

from planned.domain.entities import Message
from planned.application.repositories.base import ChangeHandler


class MessageRepositoryProtocol(Protocol):
    """Protocol defining the interface for message repositories."""

    async def get(self, date: datetime.date, key: str) -> Message:
        """Get a message by date and key."""
        ...

    async def put(self, obj: Message) -> Message:
        """Save or update a message."""
        ...

    async def search(self, date: datetime.date) -> list[Message]:
        """Search for messages on a specific date."""
        ...

    async def delete(self, obj: Message) -> None:
        """Delete a message."""
        ...

    def listen(self, handler: ChangeHandler[Message]) -> None:
        """Register a change handler for message events."""
        ...

