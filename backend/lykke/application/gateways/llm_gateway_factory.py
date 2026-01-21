"""Factory for creating LLM gateway instances based on provider."""

from loguru import logger
from lykke.core.config import settings
from lykke.core.exceptions import DomainError
from lykke.domain.value_objects.ai_chat import LLMProvider

from .llm_protocol import LLMGatewayProtocol


class LLMGatewayFactory:
    """Factory for creating LLM gateway instances."""

    @staticmethod
    def create_gateway(provider: LLMProvider) -> LLMGatewayProtocol:
        """Create an LLM gateway for the specified provider.

        Args:
            provider: The LLM provider to use

        Returns:
            An LLM gateway implementation

        Raises:
            DomainError: If the provider is not supported or API key is missing
        """
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
        raise DomainError(f"Unsupported LLM provider: {provider}")
