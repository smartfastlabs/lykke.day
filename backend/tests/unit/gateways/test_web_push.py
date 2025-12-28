"""Unit tests for WebPushGateway using dobles."""

from types import SimpleNamespace

import equals
import pytest
from dobles import InstanceDouble, allow, expect
from pydantic import AnyHttpUrl

from planned.domain.entities import PushSubscription


@pytest.mark.asyncio
async def test_send_notification(mock_web_push_gateway, test_user_uuid):
    """Test sending a push notification."""
    from uuid import UUID
    
    subscription = PushSubscription(
        user_uuid=test_user_uuid,
        device_name="Test Device",
        endpoint="https://example.com",
        p256dh="p256dh",
        auth="auth",
    )
    
    # The actual implementation would be tested here
    # This is a placeholder showing the pattern for testing with dobles
    # In practice, you'd test the actual gateway implementation
    
    assert subscription.endpoint == "https://example.com"

