"""Protocol for TriggerRepository."""

from typing import ClassVar, Protocol
from uuid import UUID

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain.entities import TacticEntity, TriggerEntity
from lykke.domain import value_objects


class TriggerRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[TriggerEntity], Protocol
):
    """Read-only protocol defining the interface for trigger repositories."""

    Query: ClassVar[type[value_objects.TriggerQuery]] = value_objects.TriggerQuery

    async def list_tactics_for_trigger(self, trigger_id: UUID) -> list[TacticEntity]:
        """Return tactics linked to a trigger."""
        ...


class TriggerRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[TriggerEntity], Protocol
):
    """Read-write protocol defining the interface for trigger repositories."""

    Query: ClassVar[type[value_objects.TriggerQuery]] = value_objects.TriggerQuery

    async def set_tactics_for_trigger(
        self, trigger_id: UUID, tactic_ids: list[UUID]
    ) -> None:
        """Replace all tactics linked to a trigger."""
        ...
