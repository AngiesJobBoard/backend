from enum import Enum


class NumEmployeesEnum(str, Enum):
    one_to_ten = "1-10"
    eleven_to_fifty = "11-50"
    fiftyone_to_twohundred = "51-200"
    twohundredone_to_fivehundred = "201-500"
    fivehundredone_to_onethousand = "501-1000"
    morethan_onethousand = "1001+"


class ScheduleType(str, Enum):
    FULL_TIME = "Full Time"
    PART_TIME = "Part Time"
    CONTRACT = "Contract"
    TEMPORARY = "Temporary"
    SEASONAL = "Seasonal"
    INTERNSHIP = "Internship"


class WeeklyScheduleType(str, Enum):
    monday_to_friday = "Monday to Friday"
    weekends_as_needed = "Weekends as Needed"
    every_weekend = "Every Weekend"
    no_weekends = "No Weekends"
    rotating_weekends = "Rotating Weekends"
    weekends_only = "Weekends Only"
    other = "Other"
    none = "None"


class ShiftType(str, Enum):
    morning = "Morning"
    day = "Day"
    evening = "Evening"
    night = "Night"
    eight_hour = "8 Hour"
    ten_hour = "10 Hour"
    twelve_hour = "12 Hour"
    other = "Other"
    none = "None"


class JobContractLength(str, Enum):
    SHORT_TERM = "Short Term"
    LONG_TERM = "Long Term"


class ResumeRequirement(str, Enum):
    required = "Required"
    optional = "Optional"
    no_resume = "No Resume"
