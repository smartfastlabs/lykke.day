"""E2E tests for SMS auth endpoints."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from lykke.app import app
from lykke.core.utils.sms_code import hash_code
from lykke.domain import value_objects
from lykke.domain.entities.sms_login_code import SmsLoginCodeEntity
from lykke.infrastructure.gateways import StubSMSGateway
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.api.routers.auth_sms import get_sms_gateway


@pytest.fixture(autouse=True)
def stub_sms_gateway():
    """Override SMS gateway to avoid sending real SMS in tests."""
    app.dependency_overrides[get_sms_gateway] = lambda: StubSMSGateway()
    yield
    app.dependency_overrides.pop(get_sms_gateway, None)


@pytest.mark.asyncio
async def test_sms_request_returns_200(test_client):
    """Test POST /auth/sms/request returns 200 (generic success, no info leak)."""
    phone = f"+1{uuid4().int % 10**10:010d}"
    response = test_client.post(
        "/auth/sms/request",
        json={"phone_number": phone},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


@pytest.mark.asyncio
async def test_sms_verify_sets_cookie_for_existing_user(test_client):
    """Test verify with valid code sets cookie for existing user."""
    import random

    from passlib.context import CryptContext

    from lykke.domain.entities import UserEntity

    code = "123456"
    phone = f"+1555{random.randint(200, 999)}{random.randint(1000, 9999)}"
    code_hash = hash_code(code)
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    # Create user first (avoids first-time user creation FK issues in test isolation)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    identity_access = UnauthenticatedIdentityAccess()
    user = UserEntity(
        email=f"sms+{phone}@test.lykke.day",
        phone_number=phone,
        hashed_password=pwd_context.hash("x"),
        is_active=True,
        is_superuser=False,
        is_verified=True,
        status=value_objects.UserStatus.ACTIVE,
    )
    await identity_access.create_user(user)

    # Insert code
    entity = SmsLoginCodeEntity(
        phone_number=phone,
        code_hash=code_hash,
        expires_at=expires_at,
    )
    await identity_access.create_sms_login_code(entity)

    response = test_client.post(
        "/auth/sms/verify",
        json={"phone_number": phone, "code": code},
    )

    assert response.status_code == 204, (
        f"Expected 204, got {response.status_code}: {response.text}"
    )
    assert "lykke_auth" in response.cookies
