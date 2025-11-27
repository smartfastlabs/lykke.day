from typing import Self


class BaseError(Exception):
    def __init__(self: Self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BaseError):
    def __init__(self: Self) -> None:
        super().__init__("not found", 404)


class PushNotificationError(BaseError):
    pass
