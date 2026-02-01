"""Gateway protocols for external services."""

from .email_provider_protocol import EmailProviderGatewayProtocol
from .domain_event_backlog_protocol import (
    DomainEventBacklogGatewayProtocol,
    DomainEventBacklogItem,
    DomainEventBacklogListResult,
)
from .google_protocol import GoogleCalendarGatewayProtocol
from .pubsub_protocol import PubSubGatewayProtocol, PubSubSubscription
from .sms_provider_protocol import SMSProviderProtocol
from .web_push_protocol import WebPushGatewayProtocol

__all__ = [
    "EmailProviderGatewayProtocol",
    "DomainEventBacklogGatewayProtocol",
    "DomainEventBacklogItem",
    "DomainEventBacklogListResult",
    "GoogleCalendarGatewayProtocol",
    "PubSubGatewayProtocol",
    "PubSubSubscription",
    "SMSProviderProtocol",
    "WebPushGatewayProtocol",
]
