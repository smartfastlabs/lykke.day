"""Helpers for building LLM tool schemas from callables."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, cast, get_type_hints

from pydantic import BaseModel, Field, create_model


def build_tool_spec_from_callable(
    on_complete: Callable[..., Any],
    tool_name: str = "on_complete",
) -> tuple[dict[str, Any], type[BaseModel]]:
    """Build a tool spec + Pydantic model from a callable signature."""
    signature = inspect.signature(on_complete)
    hints = get_type_hints(on_complete)
    fields: dict[str, tuple[Any, Any]] = {}

    for name, param in signature.parameters.items():
        if name == "self":
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise ValueError("on_complete must use explicit named parameters")

        annotation = hints.get(name, Any)
        default_value: Any = (
            ... if param.default is inspect.Parameter.empty else param.default
        )
        fields[name] = (annotation, Field(default=default_value))

    model_name = "".join(part.title() for part in tool_name.split("_")) + "Args"
    model = create_model(model_name, **cast(dict[str, Any], fields))
    schema = model.model_json_schema()
    description = on_complete.__doc__ or "Finalize the use case."
    return {"name": tool_name, "description": description, "parameters": schema}, model
