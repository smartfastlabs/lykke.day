"""Protocol for selecting an LLM gateway implementation.

The application layer should not import concrete infrastructure gateways.
Provider-to-implementation mapping is performed in an outer layer and injected
via this protocol.
"""

from __future__ import annotations

from typing import Protocol

from lykke.domain.value_objects.ai_chat import LLMProvider

from .llm_protocol import LLMGatewayProtocol


class LLMGatewayFactoryProtocol(Protocol):
    """Factory protocol for creating LLM gateways."""

    def create_gateway(self, provider: LLMProvider) -> LLMGatewayProtocol:
        """Create an LLM gateway for the specified provider."""
        ...
