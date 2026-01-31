"""Protocol for SmsLoginCodeRepository."""

from typing import Any

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

    async def mark_consumed_and_increment_attempts(
        self, code_id: Any, consumed: bool = True
    ) -> None:
        """Mark code as consumed and/or increment attempt count."""
        ...
