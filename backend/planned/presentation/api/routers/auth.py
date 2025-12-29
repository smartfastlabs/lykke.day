from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from planned.application.services import AuthService
from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.domain.value_objects.base import BaseRequestObject, BaseResponseObject
from planned.infrastructure.utils.dates import get_current_datetime

from .dependencies.services import get_auth_service
from .dependencies.user import get_current_user

router = APIRouter()


class StatusResponse(BaseResponseObject):
    ok: bool = True


class UserResponse(BaseResponseObject):
    id: str
    email: str


class RegisterRequest(BaseRequestObject):
    email: str
    password: str
    confirm_password: str


class UpdatePasswordRequest(BaseRequestObject):
    new_password: str
    confirm_new_password: str
    old_password: str | None = None


class LoginRequest(BaseRequestObject):
    email: str
    password: str


@router.post("/register")
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user. Always available (no authentication required)."""
    # Validate password confirmation
    if data.password != data.confirm_password:
        raise exceptions.BadRequestError("Passwords do not match")

    # Basic email validation
    if not data.email or "@" not in data.email:
        raise exceptions.BadRequestError("Invalid email format")

    # Create user
    user = await auth_service.create_user(data.email, data.password)

    # Automatically log in the new user
    now: str = str(get_current_datetime())
    response.set_cookie(key="logged_in_at", value=now, httponly=False, max_age=60*60*24*90)
    request.session["logged_in_at"] = now
    request.session["user_uuid"] = str(user.uuid)

    return UserResponse(id=str(user.uuid), email=user.email)


@router.post("/set-password")
async def set_password(
    data: UpdatePasswordRequest,
    user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> StatusResponse:
    """Update password for the current user."""
    if data.new_password != data.confirm_new_password:
        raise exceptions.BadRequestError("Passwords do not match")

    await auth_service.set_password(user, data.new_password)
    return StatusResponse()


@router.put("/login")
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Login with email and password."""
    user = await auth_service.authenticate_user(data.email, data.password)

    if user is None:
        raise exceptions.AuthenticationError("Invalid email or password")

    # Store session data
    now: str = str(get_current_datetime())
    response.set_cookie(key="logged_in_at", value=now, httponly=False, max_age=60*60*24*90)
    request.session["logged_in_at"] = now
    request.session["user_uuid"] = str(user.uuid)

    return UserResponse(id=str(user.uuid), email=user.email)
