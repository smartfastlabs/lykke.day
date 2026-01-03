"""Auth router for password management.

Note: Login and registration are handled by fastapi-users routes in app.py.
This router only handles password updates for authenticated users.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from planned.application.repositories import UserRepositoryProtocol
from planned.core.exceptions import BadRequestError
from planned.domain import value_objects
from planned.domain.entities import UserEntity

from .dependencies.repositories import get_user_repo
from .dependencies.user import get_current_user

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class StatusResponse(value_objects.BaseResponseObject):
    ok: bool = True


class UpdatePasswordRequest(value_objects.BaseRequestObject):
    new_password: str
    confirm_new_password: str
    old_password: str | None = None


@router.post("/set-password")
async def set_password(
    data: UpdatePasswordRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
) -> StatusResponse:
    """Update password for the current user."""
    if data.new_password != data.confirm_new_password:
        raise BadRequestError("Passwords do not match")

    # Hash and set new password
    user.hashed_password = pwd_context.hash(data.new_password)
    await user_repo.put(user)

    return StatusResponse()
