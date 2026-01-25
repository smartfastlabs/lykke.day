"""Utilities for building LLM snapshot metadata."""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from lykke.domain import value_objects


def build_referenced_entities(
    prompt_context: value_objects.LLMPromptContext,
) -> list[value_objects.LLMReferencedEntitySnapshot]:
    """Build a list of referenced entities from a prompt context."""

    seen: set[tuple[str, UUID]] = set()
    referenced: list[value_objects.LLMReferencedEntitySnapshot] = []

    def add_entities(
        entity_type: str, entities: Iterable[object | None]
    ) -> None:
        for entity in entities:
            if entity is None:
                continue
            entity_id = getattr(entity, "id", None)
            if not isinstance(entity_id, UUID):
                continue
            key = (entity_type, entity_id)
            if key in seen:
                continue
            seen.add(key)
            referenced.append(
                value_objects.LLMReferencedEntitySnapshot(
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            )

    add_entities("day", [prompt_context.day])
    add_entities("calendar_entry", prompt_context.calendar_entries)
    add_entities("task", prompt_context.tasks)
    add_entities("routine", prompt_context.routines)
    add_entities("brain_dump", prompt_context.brain_dump_items)
    add_entities("message", getattr(prompt_context, "messages", []))
    add_entities("push_notification", getattr(prompt_context, "push_notifications", []))

    return referenced
