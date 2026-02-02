"""Unit tests for UserEntity."""

from __future__ import annotations

from datetime import UTC
from uuid import uuid4

from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.events.base import EntityCreatedEvent, EntityDeletedEvent
from lykke.domain.events.user_events import UserUpdatedEvent
from lykke.domain.value_objects.update import UserUpdateObject


def test_user_post_init_normalizes_settings_dict() -> None:
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings={"timezone": "UTC"},
    )

    assert isinstance(user.settings, value_objects.UserSetting)
    assert user.settings.timezone == "UTC"


def test_user_apply_update_adds_event_and_updates_timestamp() -> None:
    user = UserEntity(email="test@example.com", hashed_password="hash")
    update = UserUpdateObject(
        email="new@example.com",
        settings_update=value_objects.UserSettingUpdate.from_dict({"timezone": "UTC"}),
    )

    updated = user.apply_update(update, UserUpdatedEvent)

    assert updated.email == "new@example.com"
    assert updated.updated_at is not None
    assert updated.updated_at.tzinfo == UTC
    events = updated.collect_events()
    assert isinstance(events[0], UserUpdatedEvent)
    assert events[0].update_object == update


def test_user_create_and_delete_emit_events() -> None:
    user = UserEntity(email="test@example.com", hashed_password="hash")

    user.create()
    events = user.collect_events()
    assert isinstance(events[0], EntityCreatedEvent)

    user.delete()
    events = user.collect_events()
    assert any(isinstance(event, EntityDeletedEvent) for event in events)


def test_user_id_property_aliases_id() -> None:
    user_id = uuid4()
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="hash")

    assert user.user_id == user_id


def test_user_settings_calendar_entry_defaults_and_merge() -> None:
    settings = value_objects.UserSetting()
    assert settings.calendar_entry_notification_settings.rules

    update = value_objects.UserSettingUpdate.from_dict(
        {"calendar_entry_notification_settings": {"enabled": False, "rules": []}}
    )
    merged = update.merge(settings)

    assert merged.calendar_entry_notification_settings.enabled is False
    assert merged.calendar_entry_notification_settings.rules == []
