from typing import Self


class BaseError(Exception):
    status_code: int = 400
    _message: str = "something went wrong"

    def __init__(self: Self, message: str | None = None) -> None:
        self.message = message or self._message
        super().__init__(self.message)


class NotFoundError(BaseError):
    status_code = 404
    _message = "not found"


class PushNotificationError(BaseError):
    status_code = 500
    _message = "push failed"


class BadRequestError(BaseError):
    status_code = 400
    _message = "bad request"


class AuthenticationError(BaseError):
    status_code = 403
    _message = "no no no"


class AuthorizationError(BaseError):
    status_code = 401
    _message = "no no no"


class ServerError(BaseError):
    status_code = 500
    _message = "oops..."


class TokenExpiredError(BaseError):
    status_code = 401
    _message = "token has expired"


# Create a namespace object for backward compatibility
class _ExceptionsNamespace:
    def __init__(self) -> None:
        self.BaseError: type[BaseError] = BaseError
        self.NotFoundError: type[NotFoundError] = NotFoundError
        self.PushNotificationError: type[PushNotificationError] = PushNotificationError
        self.BadRequestError: type[BadRequestError] = BadRequestError
        self.AuthenticationError: type[AuthenticationError] = AuthenticationError
        self.AuthorizationError: type[AuthorizationError] = AuthorizationError
        self.ServerError: type[ServerError] = ServerError
        self.TokenExpiredError: type[TokenExpiredError] = TokenExpiredError


exceptions = _ExceptionsNamespace()
