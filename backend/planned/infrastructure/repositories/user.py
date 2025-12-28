from typing import Any

from sqlalchemy import select

from planned.domain.entities import User

from .base import BaseQuery, BaseRepository
from .base.schema import users


class UserRepository(BaseRepository[User, BaseQuery]):
    """UserRepository is NOT user-scoped - it's used for user management."""
    
    Object = User
    table = users
    QueryClass = BaseQuery

    def __init__(self) -> None:
        """Initialize UserRepository without user_uuid (not user-scoped)."""
        super().__init__(user_uuid=None)  # Pass None to disable user scoping

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        async with self._get_connection(for_write=False) as conn:
            stmt = select(self.table).where(self.table.c.email == email)
            result = await conn.execute(stmt)
            row = result.mappings().first()
            
            if row is None:
                return None
            
            return self.row_to_entity(dict(row))

    @staticmethod
    def entity_to_row(user: User) -> dict[str, Any]:
        """Convert a User entity to a database row dict."""
        from datetime import UTC, datetime
        
        row: dict[str, Any] = {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
        }
        
        # Handle settings JSONB field
        if user.settings:
            row["settings"] = user.settings.model_dump(mode="json")
        else:
            from planned.domain.value_objects.user import UserSetting
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
        from uuid import UUID
        
        from planned.domain.value_objects.user import UserSetting
        
        data = dict(row)
        
        # Convert UUID to string if needed
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        
        # Handle settings - if stored as JSONB, deserialize it
        if "settings" in data and data["settings"] is not None:
            if isinstance(data["settings"], dict):
                data["settings"] = UserSetting(**data["settings"])
            elif isinstance(data["settings"], str):
                import json
                data["settings"] = UserSetting(**json.loads(data["settings"]))
        else:
            data["settings"] = UserSetting()
        
        return User.model_validate(data, from_attributes=True)

