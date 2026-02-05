"""Explicit SQLAlchemy-based identity access for unauthenticated flows.

This module is the only place where cross-user identity lookups are allowed.
It intentionally exposes *only* specific methods (no generic repository surface).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.core.exceptions import BadRequestError
from lykke.core.utils.phone_numbers import digits_only, normalize_phone_number
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import SmsLoginCodeEntity, UserEntity
from lykke.infrastructure.database.tables import User as UserDB
from lykke.infrastructure.database.tables import sms_login_codes_tbl, users_tbl
from lykke.infrastructure.database.utils import get_engine
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc


def _coerce_user_settings(raw: Any) -> value_objects.UserSetting:
    if raw is None:
        return value_objects.UserSetting()
    if isinstance(raw, dict):
        return value_objects.UserSetting.from_dict(raw)
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except Exception:
            data = None
        return value_objects.UserSetting.from_dict(data if isinstance(data, dict) else None)
    # Unknown type; default defensively
    return value_objects.UserSetting()


def _user_row_to_entity(row: dict[str, Any]) -> UserEntity:
    settings = _coerce_user_settings(row.get("settings"))
    status_raw = row.get("status")
    status = (
        value_objects.UserStatus(status_raw)
        if isinstance(status_raw, str)
        else value_objects.UserStatus.ACTIVE
    )
    data: dict[str, Any] = {
        "id": row["id"],
        "email": row["email"],
        "phone_number": row.get("phone_number"),
        "hashed_password": row["hashed_password"],
        "status": status,
        "is_active": bool(row.get("is_active", True)),
        "is_superuser": bool(row.get("is_superuser", False)),
        "is_verified": bool(row.get("is_verified", False)),
        "settings": settings,
        "created_at": row.get("created_at") or datetime.now(UTC),
        "updated_at": row.get("updated_at"),
    }
    data = ensure_datetimes_utc(data, keys=("created_at", "updated_at"))
    return UserEntity(**data)


def _user_entity_to_row(user: UserEntity) -> dict[str, Any]:
    if not user.phone_number:
        raise BadRequestError("User phone_number is required")
    status_val = user.status.value if hasattr(user.status, "value") else str(user.status)
    return {
        "id": user.id,
        "email": user.email,
        "phone_number": user.phone_number,
        "hashed_password": user.hashed_password,
        "status": status_val,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "settings": dataclass_to_json_dict(user.settings),
        "created_at": user.created_at or datetime.now(UTC),
        "updated_at": user.updated_at,
    }


def _sms_row_to_entity(row: dict[str, Any]) -> SmsLoginCodeEntity:
    data = dict(row)
    data = ensure_datetimes_utc(
        data, keys=("expires_at", "consumed_at", "created_at", "last_attempt_at")
    )
    return SmsLoginCodeEntity(**data)


def _sms_entity_to_row(entity: SmsLoginCodeEntity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "phone_number": entity.phone_number,
        "code_hash": entity.code_hash,
        "expires_at": entity.expires_at,
        "consumed_at": entity.consumed_at,
        "created_at": entity.created_at,
        "attempt_count": entity.attempt_count,
        "last_attempt_at": entity.last_attempt_at,
    }


class UnauthenticatedIdentityAccess(UnauthenticatedIdentityAccessProtocol):
    """SQLAlchemy Core/ORM implementation of UnauthenticatedIdentityAccessProtocol."""

    async def list_all_users(self) -> list[UserEntity]:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(select(users_tbl).order_by(users_tbl.c.id))
            rows = result.mappings().all()
            return [_user_row_to_entity(dict(row)) for row in rows]

    async def get_user_by_id(self, user_id: UUID) -> UserEntity | None:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(select(users_tbl).where(users_tbl.c.id == user_id))
            row = result.mappings().first()
            return _user_row_to_entity(dict(row)) if row is not None else None

    async def get_user_by_email(self, email: str) -> UserEntity | None:
        normalized = email.strip().lower()
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                select(users_tbl).where(users_tbl.c.email == normalized)
            )
            row = result.mappings().first()
            return _user_row_to_entity(dict(row)) if row is not None else None

    async def get_user_by_phone_number(self, phone_number: str) -> UserEntity | None:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                select(users_tbl).where(users_tbl.c.phone_number == phone_number)
            )
            row = result.mappings().first()
            return _user_row_to_entity(dict(row)) if row is not None else None

    async def create_user(self, user: UserEntity) -> UserEntity:
        engine = get_engine()
        row = _user_entity_to_row(user)
        async with engine.begin() as conn:
            await conn.execute(insert(users_tbl).values(**row))
        return user

    async def create_lead_user_if_new(
        self, *, email: str | None, phone_number: str | None
    ) -> None:
        """Create a lead user (status NEW_LEAD) if unique by phone/email."""
        normalized_email = email.strip().lower() if email else None
        normalized_phone = (
            normalize_phone_number(phone_number) if phone_number else None
        )

        engine = get_engine()
        async with engine.connect() as conn:
            if normalized_email:
                result = await conn.execute(
                    select(users_tbl.c.id).where(users_tbl.c.email == normalized_email)
                )
                if result.first() is not None:
                    return None
            if normalized_phone:
                result = await conn.execute(
                    select(users_tbl.c.id).where(
                        users_tbl.c.phone_number == normalized_phone
                    )
                )
                if result.first() is not None:
                    return None

        # Users require phone_number; when capturing email-only leads, use placeholder
        if not normalized_phone:
            normalized_phone = f"+1{digits_only(normalized_email or '') or uuid4().hex[:10]}"

        # Users require an email; when capturing phone-only leads, generate placeholder
        if normalized_email:
            final_email = normalized_email
        else:
            digits = digits_only(normalized_phone or "")
            token = digits if digits else uuid4().hex
            final_email = f"lead+{token}@leads.lykke.day"

        lead = UserEntity(
            email=final_email,
            phone_number=normalized_phone,
            hashed_password="!",
            is_active=False,
            is_superuser=False,
            is_verified=False,
            status=value_objects.UserStatus.NEW_LEAD,
        )
        await self.create_user(lead)
        return None

    async def create_sms_login_code(self, entity: SmsLoginCodeEntity) -> SmsLoginCodeEntity:
        engine = get_engine()
        row = _sms_entity_to_row(entity)
        async with engine.begin() as conn:
            await conn.execute(insert(sms_login_codes_tbl).values(**row))
        return entity

    async def get_latest_unconsumed_sms_login_code(
        self, phone_number: str
    ) -> SmsLoginCodeEntity | None:
        engine = get_engine()
        async with engine.connect() as conn:
            stmt = (
                select(sms_login_codes_tbl)
                .where(sms_login_codes_tbl.c.phone_number == phone_number)
                .where(sms_login_codes_tbl.c.consumed_at.is_(None))
                .order_by(sms_login_codes_tbl.c.created_at.desc())
                .limit(1)
            )
            result = await conn.execute(stmt)
            row = result.mappings().first()
            return _sms_row_to_entity(dict(row)) if row is not None else None

    async def persist_sms_login_code_attempt(self, entity: SmsLoginCodeEntity) -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            stmt = (
                update(sms_login_codes_tbl)
                .where(sms_login_codes_tbl.c.id == entity.id)
                .values(
                    attempt_count=entity.attempt_count,
                    last_attempt_at=entity.last_attempt_at,
                    consumed_at=entity.consumed_at,
                )
            )
            await conn.execute(stmt)
        return None

    async def load_user_db_for_login(self, user_id: UUID) -> UserDB | None:
        engine = get_engine()
        async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session_maker() as session:
            result = await session.execute(select(UserDB).where(UserDB.id == user_id))  # type: ignore[arg-type]
            return result.scalar_one_or_none()

