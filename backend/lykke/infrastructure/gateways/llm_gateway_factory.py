"""Infrastructure factory for creating concrete LLM gateway instances."""

from __future__ import annotations

from loguru import logger

from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMGatewayProtocol
from lykke.core.config import settings
from lykke.core.exceptions import DomainError
from lykke.domain.value_objects.ai_chat import LLMProvider


class InfraLLMGatewayFactory(LLMGatewayFactoryProtocol):
    """Selects and constructs concrete LLM gateways based on provider."""

    def create_gateway(self, provider: LLMProvider) -> LLMGatewayProtocol:
        match provider:
            case LLMProvider.ANTHROPIC:
                if not settings.ANTHROPIC_API_KEY:
                    raise DomainError("ANTHROPIC_API_KEY is not configured")
                from lykke.infrastructure.gateways.anthropic_llm import (
                    AnthropicLLMGateway,
                )

                return AnthropicLLMGateway()
            case LLMProvider.OPENAI:
                if not settings.OPENAI_API_KEY:
                    raise DomainError("OPENAI_API_KEY is not configured")
                from lykke.infrastructure.gateways.openai_llm import OpenAILLMGateway

                return OpenAILLMGateway()
