from types import SimpleNamespace

import equals
import pytest
from dobles import InstanceDouble, allow, expect
from pydantic import AnyHttpUrl
from webpush import WebPushSubscription  # type: ignore

from planned import objects
from planned.infrastructure.gateways import web_push


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_send_notification(test_user):
    from uuid import UUID
    subscription = objects.PushSubscription(
        user_uuid=UUID(test_user.id),
        device_name="Test Device",
        endpoint="https://example.com",
        p256dh="p256dh",
        auth="auth",
    )
    expect(web_push.wp).get(
        "test message",
        equals.instance_of(WebPushSubscription).with_attrs(
            endpoint=AnyHttpUrl(subscription.endpoint),
            keys=equals.anything.with_attrs(
                p256dh=subscription.p256dh,
                auth=subscription.auth,
            ),
        ),
    ).and_return(
        InstanceDouble(
            "webpush.WebPushMessage",
            endpoint=subscription.endpoint,
            encrypted="encrypted",
            headers={"header": "t"},
        )
    )

    session = InstanceDouble("aiohttp.ClientSession")
    expect(session).__aenter__().and_return(session)
    allow(session).__aexit__.and_return(None)
    expect(web_push.aiohttp).ClientSession().and_return(session)

    async def response():
        return SimpleNamespace(ok=True)

    expect(session).post(
        url=subscription.endpoint, data="encrypted", headers={"header": "t"}
    ).and_return(response())

    await web_push.send_notification(
        subscription,
        "test message",
    )
