"""Gateway protocols for external services."""

from .structured_log_backlog_protocol import (
    StructuredLogBacklogGatewayProtocol,
    StructuredLogBacklogItem,
    StructuredLogBacklogListResult,
    StructuredLogBacklogStreamGatewayProtocol,
    StructuredLogBacklogStreamSubscription,
)
from .email_provider_protocol import EmailProviderGatewayProtocol
from .google_protocol import GoogleCalendarGatewayProtocol
from .pubsub_protocol import PubSubGatewayProtocol, PubSubSubscription
from .sms_provider_protocol import SMSProviderProtocol
from .web_push_protocol import WebPushGatewayProtocol

__all__ = [
    "StructuredLogBacklogGatewayProtocol",
    "StructuredLogBacklogItem",
    "StructuredLogBacklogListResult",
    "StructuredLogBacklogStreamGatewayProtocol",
    "StructuredLogBacklogStreamSubscription",
    "EmailProviderGatewayProtocol",
    "GoogleCalendarGatewayProtocol",
    "PubSubGatewayProtocol",
    "PubSubSubscription",
    "SMSProviderProtocol",
    "WebPushGatewayProtocol",
]
