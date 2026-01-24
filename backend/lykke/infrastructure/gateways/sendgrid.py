import aiohttp
from loguru import logger

from lykke.application.gateways.email_provider_protocol import (
    EmailProviderGatewayProtocol,
)
from lykke.core.config import settings
from lykke.core.exceptions import AuthenticationError, ServerError


class SendGridGateway(EmailProviderGatewayProtocol):
    """Gateway implementing SendGrid email delivery."""

    _BASE_URL = "https://api.sendgrid.com/v3/mail/send"

    async def send_message(self, email_address: str, subject: str, body: str) -> None:
        """Send a plain text email using SendGrid's REST API."""
        api_key = settings.SENDGRID_API_KEY
        from_email = settings.SENDGRID_FROM_EMAIL

        if not api_key:
            raise AuthenticationError("SendGrid API key is not configured")
        if not from_email:
            raise ServerError("SendGrid from email is not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [
                {
                    "to": [{"email": email_address}],
                    "subject": subject,
                }
            ],
            "from": {"email": from_email},
            "content": [
                {
                    "type": "text/plain",
                    "value": body,
                }
            ],
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                self._BASE_URL,
                headers=headers,
                json=payload,
            ) as response,
        ):
            if response.status >= 400:
                error_text = await response.text()
                logger.error(
                    "SendGrid send_message failed: status={} body={}",
                    response.status,
                    error_text,
                )
                raise ServerError(
                    f"Failed to send email via SendGrid: {response.status} {response.reason}",
                )

        logger.info("SendGrid email queued for {}", email_address)
