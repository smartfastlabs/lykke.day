from fastapi import APIRouter, Depends, Request, Response

from planned import exceptions
from planned.objects import BaseRequestObject, BaseResponseObject
from planned.services import AuthService
from planned.utils.dates import get_current_datetime

from .dependencies.services import get_auth_service

router = APIRouter()


class StatusResponse(BaseResponseObject):
    ok: bool = True


class UpdatePasswordRequest(BaseRequestObject):
    new_password: str
    confirm_new_password: str
    old_password: str | None = None


@router.post("/set-password")
async def set_password(
    data: UpdatePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StatusResponse:
    if data.new_password != data.confirm_new_password:
        raise exceptions.BadRequestError()

    await auth_service.set_password(
        data.new_password,
    )
    return StatusResponse()


class LoginRequest(BaseRequestObject):
    password: str


@router.put("/login")
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> StatusResponse:
    if not await auth_service.confirm_password(
        data.password,
    ):
        raise exceptions.AuthenticationError(
            "no no no",
        )

    now: str = str(get_current_datetime())
    response.set_cookie(key="logged_in_at", value=now, httponly=False, max_age=60*60*24*90,)
    request.session["logged_in_at"] = now
    return StatusResponse()
