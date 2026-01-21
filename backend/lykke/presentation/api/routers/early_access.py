"""Public endpoint for early access lead capture."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator
from lykke.application.commands.user import CreateLeadUserCommand, CreateLeadUserHandler
from lykke.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)

from .dependencies.services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)

router = APIRouter()


class EarlyAccessRequest(BaseModel):
    """Request body for early access opt-in."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, value: EmailStr) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("email is required")
        return cleaned.lower()


class StatusResponse(BaseModel):
    """Simple OK response."""

    ok: bool = True


@router.post("/early-access", response_model=StatusResponse, status_code=200)
async def request_early_access(
    data: EarlyAccessRequest,
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
    ro_repo_factory: ReadOnlyRepositoryFactory = Depends(get_read_only_repository_factory),
) -> StatusResponse:
    """Capture lead contact as a user with status NEW_LEAD."""
    normalized_email = data.email.strip().lower()

    # Use a synthetic user id for unscoped lead creation
    synthetic_user_id: UUID = uuid4()
    ro_repos = ro_repo_factory.create(synthetic_user_id)
    handler = CreateLeadUserHandler(ro_repos, uow_factory, synthetic_user_id)

    await handler.handle(
        CreateLeadUserCommand(email=normalized_email)
    )

    return StatusResponse()

