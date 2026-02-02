"""Unit tests for PushNotificationRepository serialization (no DB required)."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from lykke.domain import value_objects
from lykke.domain.entities import PushNotificationEntity
from lykke.infrastructure.repositories.push_notification import (
    PushNotificationRepository,
)


def test_push_notification_referenced_entities_json_serializable() -> None:
    repo = PushNotificationRepository(user_id=uuid4())
    user_id = uuid4()
    referenced_entities = [
        value_objects.LLMReferencedEntitySnapshot(
            entity_type="calendar_entry",
            entity_id=uuid4(),
        )
    ]

    notification = PushNotificationEntity(
        id=uuid4(),
        user_id=user_id,
        push_subscription_ids=[uuid4()],
        content='{"title": "Test", "body": "Body"}',
        status="success",
        sent_at=datetime(2026, 2, 2, 9, 10, 6, tzinfo=UTC),
        referenced_entities=referenced_entities,
        llm_snapshot=value_objects.LLMRunResultSnapshot(
            current_time=datetime(2026, 2, 2, 9, 10, 6, tzinfo=UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            referenced_entities=referenced_entities,
        ),
    )

    row = repo.entity_to_row(notification)

    assert isinstance(row["referenced_entities"], list)
    assert row["referenced_entities"][0]["entity_type"] == "calendar_entry"
    assert row["referenced_entities"][0]["entity_id"] == str(
        referenced_entities[0].entity_id
    )
    json.dumps(row["referenced_entities"])

    assert isinstance(row["llm_snapshot"], dict)
    assert isinstance(row["llm_snapshot"]["referenced_entities"], list)
    json.dumps(row["llm_snapshot"])
