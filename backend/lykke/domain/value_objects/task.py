from dataclasses import dataclass
from datetime import time
from enum import Enum

from .base import BaseValueObject


class TaskTag(str, Enum):
    AVOIDANT = "AVOIDANT"
    FORGETTABLE = "FORGETTABLE"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    FUN = "FUN"


class TaskFrequency(str, Enum):
    DAILY = "DAILY"
    CUSTOM_WEEKLY = "CUSTOM_WEEKLY"
    WEEKLY = "WEEKLY"
    ONCE = "ONCE"
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    BI_WEEKLY = "BI_WEEKLY"
    WEEK_DAYS = "WORK_DAYS"
    WEEKEND_DAYS = "WEEKENDS"


class TaskCategory(str, Enum):
    # Personal Care
    HYGIENE = "HYGIENE"
    GROOMING = "GROOMING"
    SLEEP = "SLEEP"
    # Health & Fitness
    HEALTH = "HEALTH"
    FITNESS = "FITNESS"
    MEDICAL = "MEDICAL"
    # Nutrition
    NUTRITION = "NUTRITION"
    COOKING = "COOKING"
    # Home & Household
    HOUSE = "HOUSE"
    CLEANING = "CLEANING"
    MAINTENANCE = "MAINTENANCE"
    ORGANIZATION = "ORGANIZATION"
    # Work & Professional
    WORK = "WORK"
    MEETING = "MEETING"
    PROFESSIONAL = "PROFESSIONAL"
    # Social & Family
    FAMILY = "FAMILY"
    SOCIAL = "SOCIAL"
    RELATIONSHIP = "RELATIONSHIP"
    # Shopping & Errands
    SHOPPING = "SHOPPING"
    ERRAND = "ERRAND"
    # Transportation
    COMMUTE = "COMMUTE"
    TRAVEL = "TRAVEL"
    # Entertainment & Leisure
    ENTERTAINMENT = "ENTERTAINMENT"
    HOBBY = "HOBBY"
    RECREATION = "RECREATION"
    # Education & Learning
    EDUCATION = "EDUCATION"
    LEARNING = "LEARNING"
    # Finance & Bills
    FINANCE = "FINANCE"
    BILLS = "BILLS"
    # Technology & Digital
    TECHNOLOGY = "TECHNOLOGY"
    DIGITAL = "DIGITAL"
    # Pet Care
    PET = "PET"
    # Other
    PLANNING = "PLANNING"
    ADMIN = "ADMIN"


class EventCategory(str, Enum):
    WORK = "WORK"
    PERSONAL = "PERSONAL"
    FAMILY = "FAMILY"
    SOCIAL = "SOCIAL"
    OTHER = "OTHER"


class TaskType(str, Enum):
    ADHOC = "ADHOC"
    MEAL = "MEAL"
    WORK = "WORK"
    MEETING = "MEETING"
    EXERCISE = "EXERCISE"
    EVENT = "EVENT"
    SOCIAL = "SOCIAL"
    CHORE = "CHORE"
    ERRAND = "ERRAND"
    SHOPPING = "SHOPPING"
    PERSONAL_CARE = "PERSONAL_CARE"
    ACTIVITY = "ACTIVITY"
    ENTERTAINMENT = "ENTERTAINMENT"
    LEARNING = "LEARNING"
    COMMUTE = "COMMUTE"
    TRAVEL = "TRAVEL"
    APPOINTMENT = "APPOINTMENT"
    COMMUNICATION = "COMMUNICATION"
    FINANCIAL = "FINANCIAL"
    MAINTENANCE = "MAINTENANCE"
    PLANNING = "PLANNING"
    TECHNOLOGY = "TECHNOLOGY"


class TaskStatus(str, Enum):
    COMPLETE = "COMPLETE"
    NOT_READY = "NOT_READY"
    READY = "READY"
    PUNT = "PUNT"
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"


# TimeWindow defines task timing fields (see routine_definition.py)
