import pydantic

from planned.domain.entities.base import BaseObject


class BaseValueObject(BaseObject):
    pass


class BaseRequestObject(BaseValueObject):
    pass


class BaseResponseObject(BaseValueObject):
    pass

