from enum import Enum


class AlarmType(str, Enum):
    GENTLE = "GENTLE"
    FIRM = "FIRM"
    LOUD = "LOUD"
    SIREN = "SIREN"

