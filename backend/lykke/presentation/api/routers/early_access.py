"""Public endpoint for early access lead capture."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.presentation.api.schemas import (
    EarlyAccessRequestSchema,
    StatusResponseSchema,
)
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess

router = APIRouter()


def get_identity_access() -> UnauthenticatedIdentityAccessProtocol:
    """Identity access for unauthenticated endpoints (override in tests)."""
    return UnauthenticatedIdentityAccess()


@router.post("/early-access", response_model=StatusResponseSchema, status_code=200)
async def request_early_access(
    data: EarlyAccessRequestSchema,
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
) -> StatusResponseSchema:
    """Capture lead contact as a user with status NEW_LEAD."""
    # Create or no-op if already exists; cross-user access is isolated here.
    await identity_access.create_lead_user_if_new(
        email=data.email, phone_number=data.phone_number
    )

    return StatusResponseSchema()
