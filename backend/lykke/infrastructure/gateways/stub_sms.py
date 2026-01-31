"""Stub implementation of SMSProvider for testing."""


class StubSMSGateway:
    """Stub SMS gateway that does nothing (no-op send)."""

    async def send_message(self, phone_number: str, message: str) -> None:
        """Do nothing (no-op)."""
        pass
