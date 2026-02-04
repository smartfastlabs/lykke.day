"""SMS login code entity for one-time verification codes."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.events.base import EntityUpdatedEvent
from lykke.domain.value_objects.update import BaseUpdateObject

# System user for SMS codes (no real user)
_SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@dataclass(kw_only=True)
class SmsLoginCodeUpdateObject(BaseUpdateObject):
    """No-op update object for SmsLoginCode (codes are not updated via apply_update)."""

    pass


@dataclass(kw_only=True)
class SmsLoginCodeEntity(
    BaseEntityObject[
        SmsLoginCodeUpdateObject, EntityUpdatedEvent[SmsLoginCodeUpdateObject]
    ]
):
    """Ephemeral entity for SMS login code verification.

    Codes are hashed before storage. Not an aggregate root (no domain events).
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=_SYSTEM_USER_ID)  # system user for SMS codes
    phone_number: str
    code_hash: str
    expires_at: datetime
    consumed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attempt_count: int = 0
    last_attempt_at: datetime | None = None

    def record_verification_attempt(self, consumed: bool = False) -> None:
        """Record a verification attempt and optionally mark as consumed.

        Increments attempt_count, sets last_attempt_at, and optionally sets
        consumed_at when the code was successfully verified. Adds
        EntityUpdatedEvent so UoW persists the change.
        """
        self.attempt_count += 1
        self.last_attempt_at = datetime.now(UTC)
        if consumed:
            self.consumed_at = datetime.now(UTC)
        self.add_event(
            EntityUpdatedEvent[SmsLoginCodeUpdateObject](
                user_id=self.user_id,
                update_object=SmsLoginCodeUpdateObject(),
            )
        )
