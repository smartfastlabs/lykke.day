import asyncio
from typing import cast
from uuid import UUID

from loguru import logger

from planned.application.repositories.base import ChangeEvent, ChangeHandler
from planned.domain.entities import User
from planned.infrastructure.repositories import UserRepository

from .sheppard import SheppardService


class SheppardManager:
    """Manages per-user SheppardService instances.

    Listens to UserRepository events to automatically start/stop services
    as users are created/deleted. Each user gets their own isolated SheppardService.
    """

    def __init__(self) -> None:
        """Initialize the SheppardManager."""
        self._services: dict[UUID, tuple[SheppardService, asyncio.Task]] = {}
        self._user_repo = UserRepository()
        self._is_running = False
        self._event_handler: ChangeHandler[User] | None = None

    async def _create_service_for_user(self, user_uuid: UUID) -> SheppardService:
        """Create a SheppardService instance for a specific user.

        Args:
            user_uuid: The UUID of the user to create a service for.

        Returns:
            A configured SheppardService instance for the user.
        """
        from planned.application.repositories import (
            AuthTokenRepositoryProtocol,
            CalendarRepositoryProtocol,
            DayRepositoryProtocol,
            DayTemplateRepositoryProtocol,
            EventRepositoryProtocol,
            MessageRepositoryProtocol,
            PushSubscriptionRepositoryProtocol,
            TaskRepositoryProtocol,
            UserRepositoryProtocol,
        )
        from planned.application.services import (
            CalendarService,
            DayService,
            PlanningService,
        )
        from planned.core.exceptions import NotFoundError
        from planned.domain.entities import Alarm, DayTemplate
        from planned.domain.value_objects.alarm import AlarmType
        from planned.infrastructure.gateways.adapters import (
            GoogleCalendarGatewayAdapter,
            WebPushGatewayAdapter,
        )
        from planned.infrastructure.repositories import (
            AuthTokenRepository,
            CalendarRepository,
            DayRepository,
            DayTemplateRepository,
            EventRepository,
            MessageRepository,
            PushSubscriptionRepository,
            RoutineRepository,
            TaskDefinitionRepository,
            TaskRepository,
        )
        from planned.infrastructure.utils.dates import get_current_date
        from datetime import time

        # Create repositories scoped to user
        auth_token_repo: AuthTokenRepositoryProtocol = cast(
            "AuthTokenRepositoryProtocol", AuthTokenRepository(user_uuid=user_uuid)
        )
        calendar_repo: CalendarRepositoryProtocol = cast(
            "CalendarRepositoryProtocol", CalendarRepository(user_uuid=user_uuid)
        )
        day_repo: DayRepositoryProtocol = cast(
            "DayRepositoryProtocol", DayRepository(user_uuid=user_uuid)
        )
        day_template_repo: DayTemplateRepositoryProtocol = cast(
            "DayTemplateRepositoryProtocol",
            DayTemplateRepository(user_uuid=user_uuid),
        )
        event_repo: EventRepositoryProtocol = cast(
            "EventRepositoryProtocol", EventRepository(user_uuid=user_uuid)
        )
        message_repo: MessageRepositoryProtocol = cast(
            "MessageRepositoryProtocol", MessageRepository(user_uuid=user_uuid)
        )
        push_subscription_repo: PushSubscriptionRepositoryProtocol = cast(
            "PushSubscriptionRepositoryProtocol",
            PushSubscriptionRepository(user_uuid=user_uuid),
        )
        task_repo: TaskRepositoryProtocol = cast(
            "TaskRepositoryProtocol", TaskRepository(user_uuid=user_uuid)
        )

        # Ensure default DayTemplate exists for user
        try:
            await day_template_repo.get("default")
        except NotFoundError:
            # Template doesn't exist, create it
            default_template = DayTemplate(
                user_uuid=user_uuid,
                id="default",
                tasks=[],
                alarm=Alarm(
                    name="Default Alarm",
                    time=time(7, 15),
                    type=AlarmType.FIRM,
                ),
            )
            await day_template_repo.put(default_template)

        # Create gateway adapters
        google_gateway = GoogleCalendarGatewayAdapter()
        web_push_gateway = WebPushGatewayAdapter()

        # Create services
        calendar_service = CalendarService(
            auth_token_repo=auth_token_repo,
            calendar_repo=calendar_repo,
            event_repo=event_repo,
            google_gateway=google_gateway,
        )

        planning_service = PlanningService(
            user_uuid=user_uuid,
            user_repo=cast("UserRepositoryProtocol", self._user_repo),
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            routine_repo=cast(
                "RoutineRepositoryProtocol", RoutineRepository(user_uuid=user_uuid)
            ),
            task_definition_repo=cast(
                "TaskDefinitionRepositoryProtocol",
                TaskDefinitionRepository(user_uuid=user_uuid),
            ),
            task_repo=task_repo,
        )

        # Create day service for current date
        day_svc = await DayService.for_date(
            get_current_date(),
            user_uuid=user_uuid,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            task_repo=task_repo,
            user_repo=cast("UserRepositoryProtocol", self._user_repo),
        )

        # Load push subscriptions
        push_subscriptions = await push_subscription_repo.all()

        # Create and return SheppardService
        return SheppardService(
            day_svc=day_svc,
            push_subscription_repo=push_subscription_repo,
            task_repo=task_repo,
            calendar_service=calendar_service,
            planning_service=planning_service,
            day_repo=day_repo,
            day_template_repo=day_template_repo,
            event_repo=event_repo,
            message_repo=message_repo,
            web_push_gateway=web_push_gateway,
            push_subscriptions=push_subscriptions,
            mode="starting",
        )

    async def _handle_user_event(
        self, _sender: object | None = None, *, event: ChangeEvent[User]
    ) -> None:
        """Handle user creation/deletion events.

        Args:
            _sender: The sender of the event (unused).
            event: The change event containing the user and event type.
        """
        user = event.value
        user_uuid = UUID(user.id)

        if event.type == "create":
            await self._start_service_for_user(user_uuid)
        elif event.type == "delete":
            await self._stop_service_for_user(user_uuid)

    async def _start_service_for_user(self, user_uuid: UUID) -> None:
        """Start a SheppardService for a user.

        Args:
            user_uuid: The UUID of the user to start a service for.
        """
        if user_uuid in self._services:
            logger.warning(
                f"SheppardService already exists for user {user_uuid}, skipping"
            )
            return

        try:
            logger.info(f"Starting SheppardService for user {user_uuid}")
            service = await self._create_service_for_user(user_uuid)
            task = asyncio.create_task(service.run())
            self._services[user_uuid] = (service, task)
            logger.info(f"SheppardService started for user {user_uuid}")
        except Exception as e:
            logger.exception(
                f"Failed to start SheppardService for user {user_uuid}: {e}"
            )

    async def _stop_service_for_user(self, user_uuid: UUID) -> None:
        """Stop and remove a SheppardService for a user.

        Args:
            user_uuid: The UUID of the user to stop the service for.
        """
        if user_uuid not in self._services:
            logger.warning(
                f"No SheppardService found for user {user_uuid}, skipping"
            )
            return

        try:
            logger.info(f"Stopping SheppardService for user {user_uuid}")
            service, task = self._services[user_uuid]
            service.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._services[user_uuid]
            logger.info(f"SheppardService stopped for user {user_uuid}")
        except Exception as e:
            logger.exception(
                f"Error stopping SheppardService for user {user_uuid}: {e}"
            )
            # Clean up even if there was an error
            if user_uuid in self._services:
                del self._services[user_uuid]

    async def start(self) -> None:
        """Start the manager and all existing user services."""
        if self._is_running:
            logger.warning("SheppardManager is already running")
            return

        self._is_running = True

        # Listen to UserRepository events
        self._event_handler = self._handle_user_event
        self._user_repo.listen(self._event_handler)
        logger.info("SheppardManager listening to UserRepository events")

        # Start services for all existing users
        try:
            users = await self._user_repo.all()
            logger.info(f"Found {len(users)} existing users, starting services...")
            for user in users:
                user_uuid = UUID(user.id)
                await self._start_service_for_user(user_uuid)
            logger.info(
                f"SheppardManager started with {len(self._services)} service(s)"
            )
        except Exception as e:
            logger.exception(f"Error starting SheppardManager: {e}")
            raise

    async def stop(self) -> None:
        """Stop the manager and all user services."""
        if not self._is_running:
            return

        self._is_running = False

        # Disconnect from UserRepository events
        if self._event_handler is not None:
            UserRepository.signal_source.disconnect(self._event_handler)
            self._event_handler = None
            logger.info("SheppardManager disconnected from UserRepository events")

        # Stop all services
        logger.info(f"Stopping {len(self._services)} SheppardService instance(s)...")
        user_uuids = list(self._services.keys())
        for user_uuid in user_uuids:
            await self._stop_service_for_user(user_uuid)

        logger.info("SheppardManager stopped")

