from fastapi import APIRouter

from . import auth, days, events, google, planning, push_subscriptions, sheppard, tasks

router = APIRouter()
router.include_router(
    sheppard.router,
    prefix="/sheppard",
    tags=[
        "routine",
        "alarms",
        "planning",
    ],
)

router.include_router(
    planning.router,
    prefix="/planning",
    tags=["routine"],
)

router.include_router(
    auth.router,
    prefix="/auth",
    tags=[
        "auth",
        "login",
        "password",
    ],
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

router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
)

router.include_router(
    days.router,
    prefix="/days",
    tags=[
        "day",
        "scheduling",
        "planning",
    ],
)
