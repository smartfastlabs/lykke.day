"""Protocol for generic email provider gateway."""

from typing import Protocol


class EmailProviderGatewayProtocol(Protocol):
    """Protocol defining the interface for email provider gateways."""

    async def send_message(self, email_address: str, subject: str, body: str) -> None:
        """Send a plain text email message.

        Args:
            email_address: Destination email address.
            subject: Subject line for the email.
            body: Plain text body content for the email.
        """

        ...
