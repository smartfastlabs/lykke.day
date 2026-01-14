"""Chatbot command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends

from lykke.application.commands.chatbot import SendMessageHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_send_message_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> SendMessageHandler:
    """Get a SendMessageHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SendMessageHandler(ro_repos, uow_factory, user.id)
