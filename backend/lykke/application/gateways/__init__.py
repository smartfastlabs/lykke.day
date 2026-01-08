"""Gateway protocols for external services."""

from .email_provider_protocol import EmailProviderGatewayProtocol
from .google_protocol import GoogleCalendarGatewayProtocol
from .sms_provider_protocol import SMSProviderProtocol
from .web_push_protocol import WebPushGatewayProtocol

__all__ = [
    "EmailProviderGatewayProtocol",
    "GoogleCalendarGatewayProtocol",
    "SMSProviderProtocol",
    "WebPushGatewayProtocol",
]

