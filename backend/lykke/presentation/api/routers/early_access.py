"""Public endpoint for early access lead capture."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator

from lykke.application.commands.user import CreateLeadUserCommand, CreateLeadUserHandler
from lykke.application.unit_of_work import (  # noqa: TC001
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from lykke.presentation.handler_factory import CommandHandlerFactory

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


def get_synthetic_user_id() -> UUID:
    """Generate a synthetic user id for early access lead creation."""
    return uuid4()


def get_early_access_command_handler_factory(
    synthetic_user_id: Annotated[UUID, Depends(get_synthetic_user_id)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> CommandHandlerFactory:
    """Create a CommandHandlerFactory for early access requests."""
    return CommandHandlerFactory(
        user_id=synthetic_user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


@router.post("/early-access", response_model=StatusResponse, status_code=200)
async def request_early_access(
    data: EarlyAccessRequest,
    command_handler_factory: Annotated[
        CommandHandlerFactory, Depends(get_early_access_command_handler_factory)
    ],
) -> StatusResponse:
    """Capture lead contact as a user with status NEW_LEAD."""
    normalized_email = data.email.strip().lower()

    handler = command_handler_factory.create(CreateLeadUserHandler)
    await handler.handle(CreateLeadUserCommand(email=normalized_email))

    return StatusResponse()
