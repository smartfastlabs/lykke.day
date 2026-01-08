import aiohttp
from loguru import logger

from lykke.application.gateways.email_provider_protocol import (
    EmailProviderGatewayProtocol,
)
from lykke.core.config import settings
from lykke.core.exceptions import AuthenticationError, ServerError


class MailGunGateway(EmailProviderGatewayProtocol):
    """Gateway implementing Mailgun email delivery."""

    _BASE_URL = "https://api.mailgun.net/v3"

    async def send_message(self, email_address: str, subject: str, body: str) -> None:
        """Send a plain text email using Mailgun's REST API."""
        api_key = settings.MAILGUN_API_KEY
        domain = settings.MAILGUN_DOMAIN
        from_email = settings.MAILGUN_FROM_EMAIL

        if not api_key:
            raise AuthenticationError("Mailgun API key is not configured")
        if not domain:
            raise ServerError("Mailgun domain is not configured")
        if not from_email:
            raise ServerError("Mailgun from email is not configured")

        url = f"{self._BASE_URL}/{domain}/messages"
        data = {
            "from": from_email,
            "to": email_address,
            "subject": subject,
            "text": body,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=data,
                auth=aiohttp.BasicAuth("api", api_key),
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        "Mailgun send_message failed: status={} body={}",
                        response.status,
                        error_text,
                    )
                    raise ServerError(
                        f"Failed to send email via Mailgun: {response.status} {response.reason}",
                    )

        logger.info("Mailgun email queued for {}", email_address)


