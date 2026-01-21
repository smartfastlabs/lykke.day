from dataclasses import dataclass
from datetime import time
from enum import Enum
from uuid import UUID


class TimeBlockType(str, Enum):
    WORK = "WORK"
    BREAK = "BREAK"
    MEAL = "MEAL"
    EXERCISE = "EXERCISE"
    COMMUTE = "COMMUTE"
    MEETING = "MEETING"
    FOCUS = "FOCUS"
    ADMIN = "ADMIN"
    CREATIVE = "CREATIVE"
    LEARNING = "LEARNING"
    SOCIAL = "SOCIAL"
    PERSONAL = "PERSONAL"
    ROUTINE = "ROUTINE"
    SLEEP = "SLEEP"
    OTHER = "OTHER"


class TimeBlockCategory(str, Enum):
    # Work-related
    WORK = "WORK"
    PROFESSIONAL = "PROFESSIONAL"
    MEETING = "MEETING"
    # Personal Care
    PERSONAL_CARE = "PERSONAL_CARE"
    HEALTH = "HEALTH"
    FITNESS = "FITNESS"
    NUTRITION = "NUTRITION"
    SLEEP = "SLEEP"
    # Household
    HOUSEHOLD = "HOUSEHOLD"
    CHORES = "CHORES"
    MAINTENANCE = "MAINTENANCE"
    # Social & Family
    FAMILY = "FAMILY"
    SOCIAL = "SOCIAL"
    RELATIONSHIP = "RELATIONSHIP"
    # Entertainment & Leisure
    ENTERTAINMENT = "ENTERTAINMENT"
    HOBBY = "HOBBY"
    RECREATION = "RECREATION"
    # Education & Learning
    EDUCATION = "EDUCATION"
    LEARNING = "LEARNING"
    # Transportation
    COMMUTE = "COMMUTE"
    TRAVEL = "TRAVEL"
    # Other
    PLANNING = "PLANNING"
    ADMIN = "ADMIN"
    OTHER = "OTHER"


@dataclass(frozen=True)
class DayTemplateTimeBlock:
    """Represents a time block in a day template.

    This joins a TimeBlockDefinition to a specific time window in the template.
    Name is denormalized for performance and UI convenience.
    """

    time_block_definition_id: UUID
    start_time: time
    end_time: time
    name: str  # Denormalized from TimeBlockDefinition


@dataclass(frozen=True)
class DayTimeBlock:
    """Represents a scheduled time block on a specific day.

    This is the instance that gets created when a Day is scheduled.
    """

    time_block_definition_id: UUID
    start_time: time
    end_time: time
    name: str  # Denormalized for performance
    type: TimeBlockType  # Denormalized for performance
    category: TimeBlockCategory  # Denormalized for performance
