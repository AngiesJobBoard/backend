from enum import Enum


class LevelOfEducationEnum(str, Enum):
    HIGH_SCHOOL = "High School"
    ASSOCIATES = "Associates"
    BACHELORS = "Bachelors"
    MASTERS = "Masters"
    PHD = "PhD"
    OTHER = "Other"


class RaceEnum(str, Enum):
    WHITE = "White or Caucasian"
    INDIGENOUS = "American Indian or Alaska Native"
    MIDDLE_EASTERN = "Middle Eastern"
    BLACK = "Black"
    ASIAN = "Asian"
    HISPANIC = "Hispanic or Latino"
    PREFER_NOT_TO_SAY = "Prefer not to say"
    OTHER = "Other"


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "Non-binary"
    PREFER_NOT_TO_SAY = "Prefer not to say"
    OTHER = "Other"


class LanguageProficiencyEnum(str, Enum):
    BASIC = "Basic"
    CONVERSATIONAL = "Conversational"
    FLUENT = "Fluent"
    NATIVE = "Native"
