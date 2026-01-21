"""Query to list system templates from the file system."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.utils.templates import list_system_templates, template_display_name


@dataclass(frozen=True)
class ListSystemTemplatesQuery(Query):
    """Query to list system templates."""


@dataclass(frozen=True)
class SystemTemplatePart:
    """System template part data from file system."""

    part: str
    content: str


@dataclass(frozen=True)
class SystemTemplate:
    """System template data from file system."""

    usecase: str
    name: str
    parts: list[SystemTemplatePart]


class ListSystemTemplatesHandler(
    BaseQueryHandler[ListSystemTemplatesQuery, list[SystemTemplate]]
):
    """Lists system templates from the file system."""

    async def handle(self, query: ListSystemTemplatesQuery) -> list[SystemTemplate]:
        """List system templates from disk."""
        grouped: dict[str, list[SystemTemplatePart]] = {}
        for template in list_system_templates():
            usecase = template["usecase"]
            grouped.setdefault(usecase, []).append(
                SystemTemplatePart(part=template["part"], content=template["content"])
            )

        ordered_parts = ["system", "context", "ask"]
        templates: list[SystemTemplate] = []
        for usecase in sorted(grouped.keys()):
            parts = grouped[usecase]
            parts.sort(
                key=lambda item: ordered_parts.index(item.part)
                if item.part in ordered_parts
                else len(ordered_parts)
            )
            templates.append(
                SystemTemplate(
                    usecase=usecase,
                    name=template_display_name(usecase),
                    parts=parts,
                )
            )
        return templates
