from fastapi import APIRouter

from . import events, google, push_subscriptions, routines

router = APIRouter()

router.include_router(
    routines.router, prefix="/routines", tags=["routine", "routine-instance"]
)
router.include_router(
    google.router,
    prefix="/google",
    tags=[
        "google",
        "auth",
    ],
)

router.include_router(
    events.router,
    prefix="/events",
    tags=["events"],
)

router.include_router(
    push_subscriptions.router,
    prefix="/push",
    tags=["push", "notifications"],
)
