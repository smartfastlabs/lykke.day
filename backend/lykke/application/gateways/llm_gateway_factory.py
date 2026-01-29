"""Deprecated: LLM gateway selection has moved to infrastructure/wiring.

This module intentionally contains no infrastructure imports to preserve Clean
Architecture boundaries.
"""

from __future__ import annotations

from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)

__all__ = ["LLMGatewayFactoryProtocol"]
