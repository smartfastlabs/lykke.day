"""Unit tests for inbound SMS routing decisions."""

from lykke.domain import value_objects
from lykke.presentation.workers.tasks.inbound_sms import _should_use_sms_onboarding


def test_routes_new_lead_to_onboarding() -> None:
    assert _should_use_sms_onboarding(
        user_status=value_objects.UserStatus.NEW_LEAD, usecase_config=None
    )


def test_routes_active_state_to_onboarding() -> None:
    assert _should_use_sms_onboarding(
        user_status=value_objects.UserStatus.ACTIVE,
        usecase_config={"collection_state": {"status": "active"}},
    )


def test_does_not_route_active_user_without_state() -> None:
    assert not _should_use_sms_onboarding(
        user_status=value_objects.UserStatus.ACTIVE, usecase_config={}
    )

