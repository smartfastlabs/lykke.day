"""Repository protocol for TimeBlockDefinition entities."""

from lykke.domain import value_objects
from lykke.domain.entities import TimeBlockDefinitionEntity

from .base import ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol


class TimeBlockDefinitionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[TimeBlockDefinitionEntity]
):
    """Read-only protocol defining the interface for time block definition repositories."""

    Query = value_objects.TimeBlockDefinitionQuery


class TimeBlockDefinitionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[TimeBlockDefinitionEntity]
):
    """Read-write protocol defining the interface for time block definition repositories."""

    Query = value_objects.TimeBlockDefinitionQuery

