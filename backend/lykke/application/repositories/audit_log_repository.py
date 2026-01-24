"""Repository protocol for AuditLog entities."""

from lykke.application.repositories.base import ReadOnlyRepositoryProtocol
from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity


class AuditLogRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[AuditLogEntity]):
    """Read-only protocol defining the interface for audit log repositories."""

    Query = value_objects.AuditLogQuery
