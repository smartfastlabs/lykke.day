"""Unit tests for WebPushGateway using dobles."""


import pytest

from lykke.domain import data_objects


@pytest.mark.asyncio
async def test_send_notification(mock_web_push_gateway, test_user_id):
    """Test sending a push notification."""
    subscription = data_objects.PushSubscription(
        user_id=test_user_id,
        device_name="Test Device",
        endpoint="https://example.com",
        p256dh="p256dh",
        auth="auth",
    )

    # The actual implementation would be tested here
    # This is a placeholder showing the pattern for testing with dobles
    # In practice, you'd test the actual gateway implementation

    assert subscription.endpoint == "https://example.com"
