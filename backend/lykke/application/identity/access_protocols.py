"""Protocols for explicit identity access (unauthenticated + current-user).

These protocols intentionally expose *only* the minimal methods needed for:
- unauthenticated/login/user-creation flows (cross-user lookups allowed)
- authenticated user self-management (current-user only)

They replace unscoped repositories like UserRepository and SmsLoginCodeRepository.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from lykke.domain.entities import SmsLoginCodeEntity, UserEntity


class UnauthenticatedIdentityAccessProtocol(Protocol):
    """Cross-user identity access for unauthenticated / integration flows."""

    async def list_all_users(self) -> list[UserEntity]:
        ...

    async def get_user_by_id(self, user_id: UUID) -> UserEntity | None:
        ...

    async def get_user_by_email(self, email: str) -> UserEntity | None:
        ...

    async def get_user_by_phone_number(self, phone_number: str) -> UserEntity | None:
        ...

    async def create_user(self, user: UserEntity) -> UserEntity:
        ...

    async def create_lead_user_if_new(
        self, *, email: str | None, phone_number: str | None
    ) -> None:
        ...

    async def create_sms_login_code(self, entity: SmsLoginCodeEntity) -> SmsLoginCodeEntity:
        ...

    async def get_latest_unconsumed_sms_login_code(
        self, phone_number: str
    ) -> SmsLoginCodeEntity | None:
        ...

    async def persist_sms_login_code_attempt(self, entity: SmsLoginCodeEntity) -> None:
        ...

    async def load_user_db_for_login(self, user_id: UUID) -> object | None:
        """Return ORM user row for auth backend login (fastapi-users)."""
        ...


class CurrentUserAccessProtocol(Protocol):
    """Authenticated user self-access (current user only)."""

    async def update_user(self, updated: UserEntity) -> UserEntity:
        ...

