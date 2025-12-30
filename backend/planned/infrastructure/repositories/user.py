import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.domain.value_objects.query import BaseQuery
from planned.domain.value_objects.repository_event import RepositoryEvent
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.database.tables import users_tbl
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import BaseRepository


class UserRepository(BaseRepository[User, BaseQuery]):
    """UserRepository is NOT user-scoped - it's used for user management.

    Note: This repository overrides base methods because the User table uses 'id'
    instead of 'uuid' (fastapi-users convention).
    """

    Object = User
    table = users_tbl
    QueryClass = BaseQuery

    def __init__(self) -> None:
        """Initialize UserRepository without user scoping."""
        super().__init__()

    async def get(self, key: UUID) -> User:
        """Get a user by id (uuid)."""
        async with self._get_connection(for_write=False) as conn:
            # The database uses 'id' column (fastapi-users convention)
            stmt = select(self.table).where(self.table.c.id == key)

            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                raise exceptions.NotFoundError(f"User with id {key} not found")

            return self.row_to_entity(dict(row))

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table).where(self.table.c.email == email)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                return None

            return self.row_to_entity(dict(row))

    async def put(self, obj: User) -> User:
        """Save or update a user."""
        row = self.entity_to_row(obj)

        async with self._get_connection(for_write=True) as conn:
            # Check if object exists using 'id' column (maps to entity's uuid)
            stmt = select(self.table.c.id).where(self.table.c.id == obj.uuid)
            result = await conn.execute(stmt)
            exists = result.first() is not None

            # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            insert_stmt = pg_insert(self.table).values(**row)
            # Exclude only id from update
            update_dict = {k: v for k, v in row.items() if k != "id"}
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=update_dict,
            )
            await conn.execute(upsert_stmt)

        event_type: Literal["create", "update"] = "update" if exists else "create"
        event = RepositoryEvent[User](type=event_type, value=obj)
        await self.signal_source.send_async("change", event=event)
        return obj

    async def delete(self, key: UUID | User) -> None:
        """Delete a user by id (uuid) or by object."""
        if isinstance(key, UUID):
            try:
                obj = await self.get(key)
            except exceptions.NotFoundError:
                return

            async with self._get_connection(for_write=True) as conn:
                stmt = delete(self.table).where(self.table.c.id == key)
                await conn.execute(stmt)
        else:
            obj = key
            async with self._get_connection(for_write=True) as conn:
                # Map entity's uuid to database's id column
                stmt = delete(self.table).where(self.table.c.id == obj.uuid)
                await conn.execute(stmt)

        event = RepositoryEvent[User](type="delete", value=obj)
        await self.signal_source.send_async("change", event=event)

    @staticmethod
    def entity_to_row(user: User) -> dict[str, Any]:
        """Convert a User entity to a database row dict."""
        row: dict[str, Any] = {
            # Map entity's uuid to database's id column (fastapi-users convention)
            "id": user.uuid,
            "email": user.email,
            "phone_number": user.phone_number,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        }

        # Handle settings JSONB field
        if user.settings:
            row["settings"] = user.settings.model_dump(mode="json")
        else:
            row["settings"] = UserSetting().model_dump(mode="json")

        # Set timestamps
        if hasattr(user, "created_at") and user.created_at:
            row["created_at"] = user.created_at
        else:
            row["created_at"] = datetime.now(UTC)

        if hasattr(user, "updated_at"):
            row["updated_at"] = user.updated_at

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> User:
        """Convert a database row dict to a User entity."""
        data = dict(row)

        # Map database's 'id' column to entity's 'uuid' field
        if "id" in data:
            data["uuid"] = data.pop("id")

        # Handle settings - if stored as JSONB, deserialize it
        if "settings" in data and data["settings"] is not None:
            if isinstance(data["settings"], dict):
                data["settings"] = UserSetting(**data["settings"])
            elif isinstance(data["settings"], str):
                data["settings"] = UserSetting(**json.loads(data["settings"]))
        else:
            data["settings"] = UserSetting()

        return User.model_validate(data, from_attributes=True)
