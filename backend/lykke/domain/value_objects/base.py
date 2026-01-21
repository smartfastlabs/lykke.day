from dataclasses import dataclass

from lykke.domain.entities.base import BaseObject


@dataclass(kw_only=True)
class BaseValueObject(BaseObject):
    pass


@dataclass(kw_only=True)
class BaseRequestObject(BaseValueObject):
    pass


@dataclass(kw_only=True)
class BaseResponseObject(BaseValueObject):
    pass

