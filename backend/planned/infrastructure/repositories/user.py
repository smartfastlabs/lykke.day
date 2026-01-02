import json
from datetime import UTC, datetime
from typing import Any

from planned.domain import entities, value_objects
from planned.infrastructure.database.tables import users_tbl
from sqlalchemy import select

from .base import BaseQuery, BaseRepository


class UserRepository(BaseRepository[entities.User, BaseQuery]):
    """UserRepository is NOT user-scoped - it's used for user management."""

    Object = entities.User
    table = users_tbl
    QueryClass = BaseQuery

    def __init__(self) -> None:
        """Initialize UserRepository without user scoping."""
        super().__init__()

    async def get_by_email(self, email: str) -> entities.User | None:
        """Get a user by email address."""
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table).where(self.table.c.email == email)
            result = await conn.execute(stmt)
            row = result.mappings().first()

            if row is None:
                return None

            return self.row_to_entity(dict(row))

    @staticmethod
    def entity_to_row(user: entities.User) -> dict[str, Any]:
        """Convert a User entity to a database row dict."""
        row: dict[str, Any] = {
            "id": user.id,
            "email": user.email,
            "phone_number": user.phone_number,
            "hashed_password": user.hashed_password,
        }

        # Handle settings JSONB field
        if user.settings:
            row["settings"] = user.settings.model_dump(mode="json")
        else:
            row["settings"] = value_objects.UserSetting().model_dump(mode="json")

        # Set timestamps
        if hasattr(user, "created_at") and user.created_at:
            row["created_at"] = user.created_at
        else:
            row["created_at"] = datetime.now(UTC)

        if hasattr(user, "updated_at"):
            row["updated_at"] = user.updated_at

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> entities.User:
        """Convert a database row dict to a User entity."""
        data = dict(row)

        # The users table uses 'id' as the primary key column name
        # No conversion needed - it already matches the entity field name

        # Handle settings - if stored as JSONB, deserialize it
        if "settings" in data and data["settings"] is not None:
            if isinstance(data["settings"], dict):
                data["settings"] = value_objects.UserSetting(**data["settings"])
            elif isinstance(data["settings"], str):
                data["settings"] = value_objects.UserSetting(
                    **json.loads(data["settings"])
                )
        else:
            data["settings"] = value_objects.UserSetting()

        return entities.User.model_validate(data, from_attributes=True)
