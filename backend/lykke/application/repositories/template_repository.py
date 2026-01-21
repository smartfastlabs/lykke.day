"""Protocol for TemplateRepository."""

from typing import Protocol

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities.template import TemplateEntity


class TemplateRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[TemplateEntity], Protocol
):
    """Read-only protocol defining the interface for template repositories."""

    Query: type[value_objects.TemplateQuery] = value_objects.TemplateQuery


class TemplateRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[TemplateEntity], Protocol
):
    """Read-write protocol defining the interface for template repositories."""

    Query: type[value_objects.TemplateQuery] = value_objects.TemplateQuery
