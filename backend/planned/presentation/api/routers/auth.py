"""Auth router for password management.

Note: Login and registration are handled by fastapi-users routes in app.py.
This router only handles password updates for authenticated users.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from planned.application.commands.user import UpdateUserHandler
from planned.core.exceptions import BadRequestError
from planned.domain import value_objects
from planned.domain.entities import UserEntity

from .dependencies.services import get_update_user_handler
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
    handler: Annotated[UpdateUserHandler, Depends(get_update_user_handler)],
) -> StatusResponse:
    """Update password for the current user."""
    if data.new_password != data.confirm_new_password:
        raise BadRequestError("Passwords do not match")

    # Hash and set new password
    user.hashed_password = pwd_context.hash(data.new_password)

    await handler.update_user(user_id=user.id, user_data=user)

    return StatusResponse()
