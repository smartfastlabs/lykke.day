from typing import Self


class BaseError(Exception):
    status_code: int = 400
    _message: str = "An error occurred"

    def __init__(self: Self, message: str | None = None) -> None:
        self.message = message or self._message
        super().__init__(self.message)


class NotFoundError(BaseError):
    status_code = 404
    _message = "Resource not found"


class PushNotificationError(BaseError):
    status_code = 500
    _message = "Failed to send push notification"


class BadRequestError(BaseError):
    status_code = 400
    _message = "Invalid request"


class AuthenticationError(BaseError):
    status_code = 403
    _message = "Authentication failed"


class AuthorizationError(BaseError):
    status_code = 401
    _message = "Access denied"


class ServerError(BaseError):
    status_code = 500
    _message = "An internal server error occurred"


class TokenExpiredError(BaseError):
    status_code = 401
    _message = "Token has expired"


class DomainError(BaseError):
    """Error raised when a domain invariant is violated."""

    status_code = 400
    _message = "Domain rule violation"


__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "BadRequestError",
    "BaseError",
    "DomainError",
    "NotFoundError",
    "PushNotificationError",
    "ServerError",
    "TokenExpiredError",
]
