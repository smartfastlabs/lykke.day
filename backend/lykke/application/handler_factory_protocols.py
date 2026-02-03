"""Protocols for handler factory dependencies."""

from __future__ import annotations

from typing import Protocol
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol

class BaseFactory(Protocol):
    """Base protocol for dependency factories."""

    def can_create(self, dependency_type: type[object]) -> bool:
        """Check whether the factory can create the dependency."""

    def create(self, dependency_type: type[object]) -> object:
        """Create or return the dependency."""


class CommandHandlerFactoryProtocol(BaseFactory, Protocol):
    """Protocol for creating command handlers."""

    def can_create(self, dependency_type: type[object]) -> bool:
        """Check whether the factory can create the handler."""

    def create(self, dependency_type: type[object]) -> object:
        """Create a handler instance."""


class GatewayFactoryProtocol(BaseFactory, Protocol):
    """Protocol for accessing gateway instances."""

    def can_create(self, dependency_type: type[object]) -> bool:
        """Check whether the factory can create the gateway."""

    def create(self, dependency_type: type[object]) -> object:
        """Create or return a gateway instance."""

    @property
    def google_gateway(self) -> GoogleCalendarGatewayProtocol:
        """Google Calendar gateway."""

    @property
    def web_push_gateway(self) -> WebPushGatewayProtocol:
        """Web push gateway."""

    @property
    def sms_gateway(self) -> SMSProviderProtocol:
        """SMS provider gateway."""

    @property
    def llm_gateway_factory(self) -> LLMGatewayFactoryProtocol:
        """LLM gateway factory."""
