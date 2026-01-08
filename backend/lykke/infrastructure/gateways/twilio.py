import aiohttp
from loguru import logger
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.core.config import settings
from lykke.core.exceptions import AuthenticationError, ServerError


class TwilioGateway(SMSProviderProtocol):
    """Gateway implementing Twilio SMS messaging."""

    _BASE_URL = "https://api.twilio.com/2010-04-01/Accounts"

    async def send_message(self, phone_number: str, message: str) -> None:
        """Send an SMS message using Twilio's REST API."""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_FROM_NUMBER
        messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID

        if not account_sid or not auth_token:
            raise AuthenticationError("Twilio credentials are not configured")

        if not from_number and not messaging_service_sid:
            raise ServerError(
                "TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID must be configured",
            )

        payload: dict[str, str] = {"To": phone_number, "Body": message}
        if from_number:
            payload["From"] = from_number
        if messaging_service_sid:
            payload["MessagingServiceSid"] = messaging_service_sid

        url = f"{self._BASE_URL}/{account_sid}/Messages.json"
        auth = aiohttp.BasicAuth(account_sid, auth_token)

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, data=payload) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        "Twilio send_message failed: status={} body={}",
                        response.status,
                        error_text,
                    )
                    raise ServerError(
                        f"Failed to send SMS via Twilio: {response.status} {response.reason}",
                    )

        logger.info("Twilio SMS queued for {}", phone_number)


