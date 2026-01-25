"""Helpers for rendering tool prompts."""

from __future__ import annotations

from collections.abc import Sequence

from lykke.application.gateways.llm_protocol import LLMTool


def render_tools_prompt(tools: Sequence[LLMTool]) -> str:
    """Render a short tool list for prompt injection."""
    lines: list[str] = []
    for tool in tools:
        if tool.description:
            lines.append(f"- {tool.name}: {tool.description}")
        else:
            lines.append(f"- {tool.name}")
        if tool.prompt_notes:
            for note in tool.prompt_notes:
                lines.append(f"  - {note}")
    return "\n".join(lines)
