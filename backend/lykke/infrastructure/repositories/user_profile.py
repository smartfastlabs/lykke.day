"""UserProfile repository implementation."""

from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities.user_profile import UserProfileEntity
from lykke.infrastructure.database.tables import user_profiles_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import UserScopedBaseRepository


class UserProfileRepository(
    UserScopedBaseRepository[UserProfileEntity, value_objects.UserProfileQuery]
):
    """Repository for managing structured user profile entities."""

    Object = UserProfileEntity
    table = user_profiles_tbl
    QueryClass = value_objects.UserProfileQuery

    def build_query(self, query: value_objects.UserProfileQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        return super().build_query(query)

    @staticmethod
    def entity_to_row(profile: UserProfileEntity) -> dict[str, Any]:
        """Convert a UserProfile entity to a database row dict."""
        from lykke.core.utils.serialization import dataclass_to_json_dict

        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "preferred_name": profile.preferred_name,
            "goals": list(profile.goals or []),
            "work_hours": (
                dataclass_to_json_dict(profile.work_hours) if profile.work_hours else None
            ),
            "onboarding_completed_at": profile.onboarding_completed_at,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> UserProfileEntity:
        """Convert a database row dict to a UserProfile entity."""
        data = normalize_list_fields(dict(row), UserProfileEntity)

        # Normalize goals JSONB
        raw_goals = data.get("goals")
        if raw_goals is None:
            data["goals"] = []
        elif isinstance(raw_goals, list):
            data["goals"] = [str(x) for x in raw_goals if str(x).strip()]
        else:
            data["goals"] = []

        # Deserialize work_hours value object
        raw_work_hours = data.get("work_hours")
        if isinstance(raw_work_hours, dict):
            data["work_hours"] = value_objects.WorkHours(**raw_work_hours)
        elif raw_work_hours is None:
            data["work_hours"] = None
        elif hasattr(raw_work_hours, "model_dump"):
            data["work_hours"] = value_objects.WorkHours(**raw_work_hours.model_dump())
        else:
            data["work_hours"] = None

        data = filter_init_false_fields(data, UserProfileEntity)
        data = ensure_datetimes_utc(
            data,
            keys=("created_at", "updated_at", "onboarding_completed_at"),
        )
        return UserProfileEntity(**data)

