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
from planned.domain.value_objects import UserUpdateObject

from .dependencies.commands.user import get_update_user_handler
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
    update_user_handler: Annotated[UpdateUserHandler, Depends(get_update_user_handler)],
) -> StatusResponse:
    """Update password for the current user."""
    if data.new_password != data.confirm_new_password:
        raise BadRequestError("Passwords do not match")

    # Hash and set new password
    hashed_password = pwd_context.hash(data.new_password)

    # Create update object
    update_object = UserUpdateObject(hashed_password=hashed_password)

    await update_user_handler.run(update_data=update_object)

    return StatusResponse()
