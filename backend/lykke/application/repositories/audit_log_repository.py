"""Repository protocol for AuditLog entities."""

from lykke.application.repositories.base import ReadOnlyRepositoryProtocol
from lykke.domain.entities import AuditLogEntity

AuditLogRepositoryReadOnlyProtocol = ReadOnlyRepositoryProtocol[AuditLogEntity]
