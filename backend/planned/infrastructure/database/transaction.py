"""Transaction management using context variables."""

from collections.abc import Coroutine
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncConnection

from .utils import get_engine

if TYPE_CHECKING:
    pass

# Context variable to store the active transaction connection
_transaction_connection: ContextVar[AsyncConnection | None] = ContextVar(
    "transaction_connection",
    default=None,
)


def get_transaction_connection() -> AsyncConnection | None:
    """Get the active transaction connection if one exists.

    Returns:
        The active transaction connection, or None if no transaction is active.
    """
    return _transaction_connection.get()


class TransactionManager:
    """Context manager for managing database transactions.

    This class manages a database transaction using a context variable,
    allowing nested service calls to automatically reuse the same transaction.

    Example:
        async with TransactionManager() as conn:
            # All database operations within this block use the same transaction
            await repo.put(obj1)
            await repo.put(obj2)
            # Transaction commits automatically on success
    """

    def __init__(self) -> None:
        """Initialize the transaction manager."""
        self._connection: AsyncConnection | None = None
        self._token: Token[AsyncConnection | None] | None = None
        self._is_nested = False

    async def __aenter__(self) -> AsyncConnection:
        """Enter the transaction context.

        If there's already an active transaction, reuse it (nested transaction).
        Otherwise, create a new transaction.

        Returns:
            The transaction connection.
        """
        # Check if there's already an active transaction
        existing_conn = get_transaction_connection()
        if existing_conn is not None:
            # Reuse the existing transaction (nested)
            self._is_nested = True
            self._connection = existing_conn
            return self._connection

        engine = get_engine()
        self._connection = await engine.connect()
        await self._connection.begin()

        # Set the connection in the context variable
        self._token = _transaction_connection.set(self._connection)

        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Exit the transaction context.

        For nested transactions, do nothing (let the outer transaction handle commit/rollback).
        For top-level transactions, commit on success or rollback on exception.
        """
        if self._connection is None:
            return

        # If this is a nested transaction, don't commit/rollback - let the outer transaction handle it
        if self._is_nested:
            return

        try:
            if exc_type is None:
                # Success - commit the transaction
                await self._connection.commit()
            else:
                # Exception occurred - rollback the transaction
                await self._connection.rollback()
        finally:
            # Reset the context variable
            # At this point, we know self._token is not None because
            # we only reach here if self._is_nested is False, which means
            # we created a new transaction and set self._token in __aenter__
            assert self._token is not None
            _transaction_connection.reset(self._token)

            # Close the connection
            await self._connection.close()
            self._connection = None

    def __await__(self) -> Coroutine[None, None, AsyncConnection]:
        """Make the transaction manager awaitable for use in async context managers."""
        return self.__aenter__()
