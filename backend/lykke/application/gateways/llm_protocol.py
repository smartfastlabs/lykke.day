"""Protocol for LLM gateway implementations."""

from typing import Callable, Protocol, TypeVar

T = TypeVar("T")


class LLMGatewayProtocol(Protocol):
    """Protocol defining the interface for LLM gateway implementations.

    This protocol allows the system to work with any LLM provider
    (Anthropic, OpenAI, etc.) as long as they implement this interface.
    """

    async def run_usecase(
        self,
        system_prompt: str,
        context_prompt: str,
        ask_prompt: str,
        on_complete: Callable[..., T],
    ) -> T | None:
        """Run an LLM use case and return the on_complete result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            context_prompt: The user context prompt to evaluate
            ask_prompt: The specific ask prompt for the LLM
            on_complete: Callback invoked with tool arguments

        Returns:
            The on_complete result or None if no completion was returned
        """
        raise NotImplementedError
