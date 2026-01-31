import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.infrastructure.database.tables import users_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
)

from .base import BaseRepository


class UserRepository(BaseRepository[UserEntity, value_objects.UserQuery]):
    """UserRepository is NOT user-scoped - it's used for user management."""

    Object = UserEntity
    table = users_tbl
    QueryClass = value_objects.UserQuery

    def __init__(self) -> None:
        """Initialize UserRepository without user scoping."""
        super().__init__()

    def build_query(self, query: value_objects.UserQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.email is not None:
            stmt = stmt.where(self.table.c.email == query.email)

        if query.phone_number is not None:
            stmt = stmt.where(self.table.c.phone_number == query.phone_number)

        return stmt

    @staticmethod
    def entity_to_row(user: UserEntity) -> dict[str, Any]:
        """Convert a User entity to a database row dict."""
        row: dict[str, Any] = {
            "id": user.id,
            "email": user.email,
            "phone_number": user.phone_number,
            "hashed_password": user.hashed_password,
            "status": user.status,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        }

        # Handle settings JSONB field
        if user.settings:
            row["settings"] = dataclass_to_json_dict(user.settings)
        else:
            row["settings"] = dataclass_to_json_dict(value_objects.UserSetting())

        # Set timestamps
        if hasattr(user, "created_at") and user.created_at:
            row["created_at"] = user.created_at
        else:
            row["created_at"] = datetime.now(UTC)

        if hasattr(user, "updated_at"):
            row["updated_at"] = user.updated_at

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> UserEntity:
        """Convert a database row dict to a User entity."""
        data = dict(row)

        # The users table uses 'id' as the primary key column name
        # No conversion needed - it already matches the entity field name

        # Handle settings - if stored as JSONB, deserialize it
        if "settings" in data and data["settings"] is not None:
            if isinstance(data["settings"], dict):
                data["settings"] = value_objects.UserSetting.from_dict(data["settings"])
            elif isinstance(data["settings"], str):
                raw_settings = json.loads(data["settings"])
                data["settings"] = value_objects.UserSetting.from_dict(
                    raw_settings if isinstance(raw_settings, dict) else None
                )
        else:
            data["settings"] = value_objects.UserSetting()

        if "status" not in data or data["status"] is None:
            data["status"] = value_objects.UserStatus.ACTIVE
        else:
            # Coerce raw values into enum
            data["status"] = value_objects.UserStatus(data["status"])

        data = filter_init_false_fields(data, UserEntity)
        data = ensure_datetimes_utc(data, keys=("created_at", "updated_at"))
        return UserEntity(**data)
