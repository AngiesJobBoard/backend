"""
These might be better suited as a database table, or even just json files locally
"""

from enum import Enum


class PayType(str, Enum):
    HOURLY = "Hourly"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


class WorkSettingEnum(str, Enum):
    REMOTE = "Remote"
    IN_PERSON = "In-person"
    HYBRID = "Hybrid"
    TEMPORARILY_REMOTE = "Temporarily Remote"


class JobTypeEnum(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    TEMPORARY = "Temporary"
    INTERNSHIP = "Internship"
    VOLUNTEER = "Volunteer"
