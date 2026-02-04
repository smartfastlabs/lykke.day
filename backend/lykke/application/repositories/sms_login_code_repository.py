"""Protocol for SmsLoginCodeRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import SmsLoginCodeEntity


class SmsLoginCodeRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[SmsLoginCodeEntity]
):
    """Read-only protocol for SMS login code repositories."""

    Query = value_objects.SmsLoginCodeQuery


class SmsLoginCodeRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[SmsLoginCodeEntity]
):
    """Read-write protocol for SMS login code repositories."""

    Query = value_objects.SmsLoginCodeQuery
