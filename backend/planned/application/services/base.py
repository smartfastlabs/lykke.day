from planned.domain import entities
from planned.infrastructure.database.transaction import TransactionManager


class BaseService:
    """Base class for all services.

    Provides transaction management capabilities.
    """

    user: entities.User

    def __init__(self, user: entities.User) -> None:
        """Initialize the service with a user.

        Args:
            user: The user associated with this service instance.
        """
        self.user = user

    def transaction(self) -> TransactionManager:
        """Get a transaction manager for wrapping operations in a transaction.

        Example:
            async with self.transaction():
                await self.repo.put(obj1)
                await self.repo.put(obj2)
                # Transaction commits automatically on success

        Returns:
            A TransactionManager instance that can be used as an async context manager.
        """
        return TransactionManager()
