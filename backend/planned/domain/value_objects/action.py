from enum import Enum


class ActionType(str, Enum):
    COMPLETE = "COMPLETE"
    DELETE = "DELETE"
    EDIT = "EDIT"
    NOTIFY = "NOTIFY"
    PAUSE = "PAUSE"
    PUNT = "PUNT"
    RESUME = "RESUME"
    START = "START"
    VIEW = "VIEW"

