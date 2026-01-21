"""Protocol for generic SMS providers."""

from typing import Protocol


class SMSProviderProtocol(Protocol):
    """Protocol defining the interface for SMS providers."""

    async def send_message(self, phone_number: str, message: str) -> None:
        """Send an SMS message.

        Args:
            phone_number: Destination phone number in E.164 format.
            message: Message body to send.
        """
        ...


