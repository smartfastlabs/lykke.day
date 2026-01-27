"""Unit tests for DayTemplateEntity time block helpers."""

from __future__ import annotations

from datetime import time
from uuid import uuid4

import pytest

from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayTemplateEntity


def _build_template() -> DayTemplateEntity:
    return DayTemplateEntity(
        user_id=uuid4(),
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )


def test_add_time_block_rejects_overlaps() -> None:
    template = _build_template()
    block = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=uuid4(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        name="Work",
    )
    template = template.add_time_block(block)

    overlapping = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=uuid4(),
        start_time=time(9, 30),
        end_time=time(10, 30),
        name="Overlap",
    )

    with pytest.raises(DomainError, match="overlaps with existing"):
        template.add_time_block(overlapping)


def test_remove_time_block_raises_when_missing() -> None:
    template = _build_template()

    with pytest.raises(NotFoundError, match="Time block not found"):
        template.remove_time_block(uuid4(), time(8, 0))


def test_add_time_block_accepts_non_overlap() -> None:
    template = _build_template()
    block = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=uuid4(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        name="Work",
    )

    updated = template.add_time_block(block)

    assert updated.time_blocks == [block]


def test_remove_time_block_skips_non_matching_blocks() -> None:
    template = _build_template()
    block_a = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=uuid4(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        name="Work",
    )
    block_b = value_objects.DayTemplateTimeBlock(
        time_block_definition_id=uuid4(),
        start_time=time(11, 0),
        end_time=time(12, 0),
        name="Break",
    )
    template = template.add_time_block(block_a)
    template = template.add_time_block(block_b)

    updated = template.remove_time_block(block_b.time_block_definition_id, block_b.start_time)

    assert updated.time_blocks == [block_a]
