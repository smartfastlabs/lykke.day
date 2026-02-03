"""Protocols for handler factory dependencies."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Protocol, TypeVar
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol

if TYPE_CHECKING:
    from lykke.application.commands.base import BaseCommandHandler

HandlerT = TypeVar("HandlerT", bound="BaseCommandHandler[Any, Any]")


class CommandHandlerFactoryProtocol(Protocol):
    """Protocol for creating command handlers."""

    def create(self, handler_class: type[HandlerT]) -> HandlerT:
        """Create a handler instance."""


class GatewayFactoryProtocol(Protocol):
    """Protocol for accessing gateway instances."""

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
