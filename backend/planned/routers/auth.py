from fastapi import APIRouter, Request, Response

from planned import exceptions
from planned.objects import BaseObject, Event
from planned.repositories import event_repo
from planned.services import auth_svc
from planned.utils.dates import get_current_datetime

router = APIRouter()


class StatusResponse(BaseObject):
    ok: bool = True


class UpdatePasswordRequest(BaseObject):
    new_password: str
    confirm_new_password: str
    old_password: str | None = None


@router.post("/set-password")
async def set_password(data: UpdatePasswordRequest) -> StatusResponse:
    if data.new_password != data.confirm_new_password:
        raise exceptions.BadRequestError()

    await auth_svc.set_password(
        data.new_password,
    )
    return StatusResponse()


class LoginRequest(BaseObject):
    password: str


@router.put("/login")
async def login(data: LoginRequest, request: Request, response: Response,) -> StatusResponse:
    if not await auth_svc.confirm_password(
        data.password,
    ):
        raise exceptions.AuthenticationError(
            "no no no",
        )

    now: str = str(get_current_datetime())
    response.set_cookie(key="logged_in_at", value=now, httponly=False, max_age=60*60*24*90,)
    request.session["logged_in_at"] = now
    return StatusResponse()
