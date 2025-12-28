from planned.infrastructure.database.transaction import TransactionManager


class BaseService:
    """Base class for all services.

    Provides transaction management capabilities.
    """

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
