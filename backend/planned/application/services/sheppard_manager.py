import asyncio
from datetime import time
from uuid import UUID

from loguru import logger

from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.gateways.web_push_protocol import WebPushGatewayProtocol
from planned.application.services import CalendarService, PlanningService
from planned.application.services.factories import DayServiceFactory
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.common.repository_handler import ChangeHandler
from planned.core import exceptions
from planned.domain.entities import Alarm, DayTemplate, User
from planned.domain.value_objects.alarm import AlarmType
from planned.domain.value_objects.repository_event import RepositoryEvent
from planned.infrastructure.utils.dates import get_current_date

from .sheppard import SheppardService


# TODO: Consider renaming SheppardManager to UserSchedulerManager or DaySchedulerManager
# for better clarity. "Sheppard" is unclear and doesn't convey the manager's purpose.
class SheppardManager:
    """Manages per-user SheppardService instances.

    Listens to UserRepository events to automatically start/stop services
    as users are created/deleted. Each user gets their own isolated SheppardService.
    """

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
        web_push_gateway: WebPushGatewayProtocol,
    ) -> None:
        """Initialize the SheppardManager.

        Args:
            uow_factory: Factory for creating UnitOfWork instances
            google_gateway: Gateway for Google Calendar integration
            web_push_gateway: Gateway for web push notifications
        """
        self._services: dict[UUID, tuple[SheppardService, asyncio.Task]] = {}
        self._uow_factory = uow_factory
        self._google_gateway = google_gateway
        self._web_push_gateway = web_push_gateway
        self._is_running = False
        self._event_handler: ChangeHandler[User] | None = None

    async def _create_service_for_user(self, user_id: UUID) -> SheppardService:
        """Create a SheppardService instance for a specific user.

        Args:
            user_id: The ID of the user to create a service for.

        Returns:
            A configured SheppardService instance for the user.
        """
        # Create UnitOfWork for setup operations
        uow = self._uow_factory.create(user_id)
        async with uow:
            # Ensure default DayTemplate exists for user
            try:
                await uow.day_templates.get_by_slug("default")
            except exceptions.NotFoundError:
                # Template doesn't exist, create it
                default_template = DayTemplate(
                    user_id=user_id,
                    slug="default",
                    routine_ids=[],
                    alarm=Alarm(
                        name="Default Alarm",
                        time=time(7, 15),
                        type=AlarmType.FIRM,
                    ),
                )
                await uow.day_templates.put(default_template)
                await uow.commit()

            # Get user
            user = await uow.users.get(user_id)

            # Load push subscriptions
            push_subscriptions = await uow.push_subscriptions.all()

            # Create services outside UoW context (they'll create their own when needed)
            # Create day service for current date using factory
            date = get_current_date()
            factory = DayServiceFactory(
                user=user,
                uow_factory=self._uow_factory,
            )
            day_svc = await factory.create(date, user_id=user_id)

        # Create services (they'll create their own UoW instances when needed)
        calendar_service = CalendarService(
            user=user,
            uow_factory=self._uow_factory,
            google_gateway=self._google_gateway,
        )

        planning_service = PlanningService(
            user=user,
            uow_factory=self._uow_factory,
        )

        # Create and return SheppardService
        return SheppardService(
            user=user,
            day_svc=day_svc,
            uow_factory=self._uow_factory,
            calendar_service=calendar_service,
            planning_service=planning_service,
            web_push_gateway=self._web_push_gateway,
            push_subscriptions=push_subscriptions,
            mode="starting",
        )

    async def _handle_user_event(
        self, _sender: object | None = None, *, event: RepositoryEvent[User]
    ) -> None:
        """Handle user creation/deletion events.

        Args:
            _sender: The sender of the event (unused).
            event: The change event containing the user and event type.
        """
        user = event.value
        user_id = user.id

        if event.type == "create":
            await self._start_service_for_user(user_id)
        elif event.type == "delete":
            await self._stop_service_for_user(user_id)

    async def _start_service_for_user(self, user_id: UUID) -> None:
        """Start a SheppardService for a user.

        Args:
            user_id: The ID of the user to start a service for.
        """
        if user_id in self._services:
            logger.warning(
                f"SheppardService already exists for user {user_id}, skipping"
            )
            return

        try:
            logger.info(f"Starting SheppardService for user {user_id}")
            service = await self._create_service_for_user(user_id)
            task = asyncio.create_task(service.run())
            self._services[user_id] = (service, task)
            logger.info(f"SheppardService started for user {user_id}")
        except Exception as e:
            logger.exception(f"Failed to start SheppardService for user {user_id}: {e}")

    async def _stop_service_for_user(self, user_id: UUID) -> None:
        """Stop and remove a SheppardService for a user.

        Args:
            user_id: The ID of the user to stop the service for.
        """
        if user_id not in self._services:
            logger.warning(f"No SheppardService found for user {user_id}, skipping")
            return

        try:
            logger.info(f"Stopping SheppardService for user {user_id}")
            service, task = self._services[user_id]
            service.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._services[user_id]
            logger.info(f"SheppardService stopped for user {user_id}")
        except Exception as e:
            logger.exception(f"Error stopping SheppardService for user {user_id}: {e}")
            # Clean up even if there was an error
            if user_id in self._services:
                del self._services[user_id]

    async def start(self) -> None:
        """Start the manager and all existing user services."""
        if self._is_running:
            logger.warning("SheppardManager is already running")
            return

        self._is_running = True

        # Get UserRepository to listen to events
        # UserRepository is not user-scoped, so we use a dummy user_id
        # The actual user_id doesn't matter for accessing the users repository
        dummy_uow = self._uow_factory.create(
            UUID("00000000-0000-0000-0000-000000000000")
        )
        async with dummy_uow:
            user_repo = dummy_uow.users

            # Listen to UserRepository events (signals are class-level)
            self._event_handler = self._handle_user_event
            # Access the class-level signal
            from planned.infrastructure.repositories import UserRepository

            UserRepository.signal_source.connect(self._event_handler)
            logger.info("SheppardManager listening to UserRepository events")

            # Start services for all existing users
            try:
                users = await user_repo.all()
                logger.info(f"Found {len(users)} existing users, starting services...")
                for user in users:
                    user_id = user.id
                    await self._start_service_for_user(user_id)
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
            from planned.infrastructure.repositories import UserRepository

            UserRepository.signal_source.disconnect(self._event_handler)
            self._event_handler = None
            logger.info("SheppardManager disconnected from UserRepository events")

        # Stop all services
        logger.info(f"Stopping {len(self._services)} SheppardService instance(s)...")
        user_ids = list(self._services.keys())
        for user_id in user_ids:
            await self._stop_service_for_user(user_id)

        logger.info("SheppardManager stopped")

    def get_service_for_user(self, user_id: UUID) -> SheppardService | None:
        """Get the SheppardService instance for a specific user.

        Args:
            user_id: The ID of the user to get the service for.

        Returns:
            The SheppardService instance for the user, or None if it doesn't exist.
        """
        if user_id in self._services:
            service, _ = self._services[user_id]
            return service
        return None

    async def ensure_service_for_user(self, user_id: UUID) -> SheppardService:
        """Ensure a SheppardService exists for a user, starting it if necessary.

        Args:
            user_id: The ID of the user to ensure a service for.

        Returns:
            The SheppardService instance for the user.

        Raises:
            RuntimeError: If the service cannot be started.
        """
        service = self.get_service_for_user(user_id)
        if service is None:
            await self._start_service_for_user(user_id)
            service = self.get_service_for_user(user_id)
            if service is None:
                raise RuntimeError(
                    f"Failed to start SheppardService for user {user_id}"
                )
        return service
