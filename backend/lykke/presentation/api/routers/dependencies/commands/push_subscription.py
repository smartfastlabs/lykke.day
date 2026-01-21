"""PushSubscription command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import WebPushGateway
from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user
from lykke.domain.entities import UserEntity


def get_web_push_gateway() -> WebPushGatewayProtocol:
    """Get an instance of WebPushGateway."""
    return WebPushGateway()


def get_send_push_notification_handler(
    web_push_gateway: Annotated[
        WebPushGatewayProtocol, Depends(get_web_push_gateway)
    ],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    uow_factory: Annotated[
        UnitOfWorkFactory, Depends(get_unit_of_work_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> SendPushNotificationHandler:
    """Get a SendPushNotificationHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SendPushNotificationHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user.id,
        web_push_gateway=web_push_gateway,
    )

