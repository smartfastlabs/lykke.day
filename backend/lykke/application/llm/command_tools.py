"""Helpers for building LLM tools from command handlers."""

from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from typing import Any, TypeVar, cast, get_type_hints

from pydantic import BaseModel, Field, create_model

from lykke.application.commands.base import Command, CommandHandler
from lykke.application.gateways.llm_protocol import LLMTool

CommandT = TypeVar("CommandT", bound=Command)


def build_args_model_from_command(command_type: type[CommandT]) -> type[BaseModel]:
    """Build a Pydantic args model from a Command dataclass."""
    if not is_dataclass(command_type):
        raise ValueError("Command tools require a dataclass Command type")

    hints = get_type_hints(command_type)
    model_fields: dict[str, tuple[Any, Any]] = {}
    for field in fields(command_type):
        annotation = hints.get(field.name, Any)
        if field.default is not MISSING:
            model_fields[field.name] = (annotation, Field(default=field.default))
        elif field.default_factory is not MISSING:
            model_fields[field.name] = (
                annotation,
                Field(default_factory=field.default_factory),
            )
        else:
            model_fields[field.name] = (annotation, Field(default=...))

    model_name = f"{command_type.__name__}Args"
    return create_model(model_name, **cast("dict[str, Any]", model_fields))


def make_command_tool(
    *,
    name: str,
    handler: CommandHandler[CommandT, Any],
    command_type: type[CommandT],
    description: str | None = None,
    prompt_notes: list[str] | None = None,
) -> LLMTool:
    """Create a thin LLMTool wrapper around a command handler."""
    args_model = build_args_model_from_command(command_type)

    async def _call(**kwargs: Any) -> Any:
        command = command_type(**kwargs)
        return await handler.handle(command)

    return LLMTool(
        name=name,
        callback=_call,
        description=description,
        prompt_notes=prompt_notes,
        args_model=args_model,
    )
