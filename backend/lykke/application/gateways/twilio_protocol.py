"""Protocol for Twilio SMS gateway."""

from typing import Protocol


class TwilioGatewayProtocol(Protocol):
    """Protocol defining the interface for Twilio SMS gateways."""

    async def send_message(self, phone_number: str, message: str) -> None:
        """Send an SMS message.

        Args:
            phone_number: Destination phone number in E.164 format.
            message: Message body to send.
        """
        ...


