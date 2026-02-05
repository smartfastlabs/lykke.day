"""User-scoped access for the authenticated *current user* record.

This replaces using a global/unscoped UserRepository for normal application code.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import update

from lykke.application.identity import CurrentUserAccessProtocol
from lykke.core.exceptions import AuthorizationError
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain.entities import UserEntity
from lykke.infrastructure.database.tables import users_tbl
from lykke.infrastructure.database.utils import get_engine


class CurrentUserAccess(CurrentUserAccessProtocol):
    def __init__(self, *, user: UserEntity) -> None:
        self._user_id = user.id

    async def update_user(self, updated: UserEntity) -> UserEntity:
        if updated.id != self._user_id:
            raise AuthorizationError("Cannot update another user")

        engine = get_engine()
        status_val = updated.status.value if hasattr(updated.status, "value") else str(updated.status)
        updated_at = updated.updated_at or datetime.now(UTC)

        async with engine.begin() as conn:
            await conn.execute(
                update(users_tbl)
                .where(users_tbl.c.id == self._user_id)
                .values(
                    email=updated.email,
                    phone_number=updated.phone_number,
                    hashed_password=updated.hashed_password,
                    status=status_val,
                    is_active=updated.is_active,
                    is_superuser=updated.is_superuser,
                    is_verified=updated.is_verified,
                    settings=dataclass_to_json_dict(updated.settings),
                    updated_at=updated_at,
                )
            )

        # Ensure the returned entity carries the timestamp we persisted
        if updated.updated_at is None:
            updated = updated.clone(updated_at=updated_at)
        return updated

