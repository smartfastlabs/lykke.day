"""
Dependency container for repositories and services.

This module provides a container pattern to reduce dependency injection verbosity
in route handlers by bundling related dependencies together.
"""

from typing import Annotated

from fastapi import Depends
from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarEntryRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.domain import entities

from .repositories import (
    get_auth_token_repo,
    get_calendar_entry_repo,
    get_calendar_repo,
    get_day_repo,
    get_day_template_repo,
    get_message_repo,
    get_push_subscription_repo,
    get_routine_repo,
    get_task_definition_repo,
    get_task_repo,
    get_user_repo,
)
from .user import get_current_user


class RepositoryContainer:
    """Container for all repository dependencies.

    This class bundles all repositories together to reduce verbosity
    in route handler dependency injection.
    """

    def __init__(
        self,
        user: entities.User,
        user_repo: UserRepositoryProtocol,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        calendar_entry_repo: CalendarEntryRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        task_definition_repo: TaskDefinitionRepositoryProtocol,
        routine_repo: RoutineRepositoryProtocol,
        calendar_repo: CalendarRepositoryProtocol,
        auth_token_repo: AuthTokenRepositoryProtocol,
        push_subscription_repo: PushSubscriptionRepositoryProtocol,
    ) -> None:
        """Initialize container with all repositories."""
        self.user = user
        self.user_repo = user_repo
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.calendar_entry_repo = calendar_entry_repo
        self.message_repo = message_repo
        self.task_repo = task_repo
        self.task_definition_repo = task_definition_repo
        self.routine_repo = routine_repo
        self.calendar_repo = calendar_repo
        self.auth_token_repo = auth_token_repo
        self.push_subscription_repo = push_subscription_repo


def get_repository_container(
    user: Annotated[entities.User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    calendar_entry_repo: Annotated[
        CalendarEntryRepositoryProtocol, Depends(get_calendar_entry_repo)
    ],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
    task_definition_repo: Annotated[
        TaskDefinitionRepositoryProtocol, Depends(get_task_definition_repo)
    ],
    routine_repo: Annotated[RoutineRepositoryProtocol, Depends(get_routine_repo)],
    calendar_repo: Annotated[CalendarRepositoryProtocol, Depends(get_calendar_repo)],
    auth_token_repo: Annotated[
        AuthTokenRepositoryProtocol, Depends(get_auth_token_repo)
    ],
    push_subscription_repo: Annotated[
        PushSubscriptionRepositoryProtocol, Depends(get_push_subscription_repo)
    ],
) -> RepositoryContainer:
    """Get a repository container with all repositories."""
    return RepositoryContainer(
        user=user,
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        calendar_entry_repo=calendar_entry_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        task_definition_repo=task_definition_repo,
        routine_repo=routine_repo,
        calendar_repo=calendar_repo,
        auth_token_repo=auth_token_repo,
        push_subscription_repo=push_subscription_repo,
    )
