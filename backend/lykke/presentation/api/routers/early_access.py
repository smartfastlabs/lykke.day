"""Public endpoint for early access lead capture."""

from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from lykke.application.commands.user import CreateLeadUserData, CreateLeadUserHandler
from lykke.core.exceptions import BadRequestError

from .dependencies.services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)

router = APIRouter()


class EarlyAccessRequest(BaseModel):
    """Request body for early access opt-in."""

    contact: str

    @field_validator("contact")
    @classmethod
    def contact_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("contact is required")
        return cleaned


class StatusResponse(BaseModel):
    """Simple OK response."""

    ok: bool = True


def _is_valid_email(contact: str) -> bool:
    """Basic email validation."""
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(email_regex, contact) is not None


def _normalize_phone(contact: str) -> str | None:
    """Normalize phone to digits with optional leading +."""
    digits = re.sub(r"[^\d+]", "", contact)
    # Ensure only one leading +
    if digits.count("+") > 1:
        return None
    if "+" in digits and not digits.startswith("+"):
        return None
    digits = digits.replace("+", "")
    # Basic length check (7-15 digits typical E.164)
    if not (7 <= len(digits) <= 15):
        return None
    return f"+{digits}"


@router.post("/early-access", response_model=StatusResponse, status_code=200)
async def request_early_access(
    data: EarlyAccessRequest,
    uow_factory=Depends(get_unit_of_work_factory),
    ro_repo_factory=Depends(get_read_only_repository_factory),
) -> StatusResponse:
    """Capture lead contact as a user with status NEW_LEAD."""
    contact = data.contact.strip()
    normalized_email: str | None = None
    normalized_phone: str | None = None

    if _is_valid_email(contact):
        normalized_email = contact.lower()
    else:
        normalized_phone = _normalize_phone(contact)

    if normalized_email is None and normalized_phone is None:
        raise BadRequestError("Contact must be a valid email or phone number")

    # Use a synthetic user id for unscoped lead creation
    synthetic_user_id: UUID = uuid4()
    ro_repos = ro_repo_factory.create(synthetic_user_id)
    handler = CreateLeadUserHandler(ro_repos, uow_factory, synthetic_user_id)

    await handler.run(
        CreateLeadUserData(email=normalized_email, phone_number=normalized_phone)
    )

    return StatusResponse()

