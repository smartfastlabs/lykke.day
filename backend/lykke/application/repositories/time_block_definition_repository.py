"""Repository protocol for TimeBlockDefinition entities."""

from lykke.domain import value_objects
from lykke.domain.data_objects import TimeBlockDefinition

from .base import ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol


class TimeBlockDefinitionRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[TimeBlockDefinition]
):
    """Read-only protocol defining the interface for time block definition repositories."""

    Query = value_objects.TimeBlockDefinitionQuery


class TimeBlockDefinitionRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[TimeBlockDefinition]
):
    """Read-write protocol defining the interface for time block definition repositories."""

    Query = value_objects.TimeBlockDefinitionQuery

