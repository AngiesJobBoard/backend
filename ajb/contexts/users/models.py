from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base.models import BaseDataModel
from ajb.common.models import GeneralLocation, convert_pay_to_hourly
from ajb.static.enumerations import (
    WorkSettingEnum,
    JobTypeEnum,
    PayType,
    RaceEnum,
    GenderEnum,
    LanguageProficiencyEnum,
)


class DemographicData(BaseModel):
    birth_year: int | None = None
    race: RaceEnum | None = None
    gender: GenderEnum | None = None
    has_djisability: bool | None = None
    arrest_record: bool | None = None


class ContactInformation(BaseModel):
    user_location: GeneralLocation | None = None


class JobSchedule(BaseModel):
    days: list[str]
    shifts: list[str]
    schedules: list[str]


class DesiredPay(BaseModel):
    minimum_pay: int
    pay_period: PayType

    def get_pay_as_hourly(self) -> float:
        return convert_pay_to_hourly(self.minimum_pay, self.pay_period)


class JobPreferences(BaseModel):
    desired_job_title: str | None = None
    desired_job_types: list[JobTypeEnum] | None = None
    desired_schedule: list[JobSchedule] | None = None
    desired_pay: DesiredPay | None = None
    willing_to_relocate: bool | None = None
    desired_work_settings: list[WorkSettingEnum] | None = None
    desired_industries: list[str] | None = None
    ready_to_start_immediately: bool | None = None


class WorkHistory(BaseModel):
    job_title: str
    company_name: str
    job_industry: str | None = None
    still_at_job: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Education(BaseModel):
    school_name: str
    level_of_education: str
    field_of_study: str
    still_in_school: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Skill(BaseModel):
    skill: str
    years_experience: int


class License(BaseModel):
    license_name: str
    expiration_date_month: int | None = None
    expiration_date_year: str | None = None
    does_not_expire: bool


class Certification(BaseModel):
    certification_name: str
    expiration_date_month: int | None = None
    expiration_date_year: str | None = None
    does_not_expire: bool


class Langauge(BaseModel):
    language: str
    language_proficiency: LanguageProficiencyEnum


class Qualifications(BaseModel):
    most_recent_job: WorkHistory | None = None
    work_history: list[WorkHistory] | None = None
    education: list[Education] | None = None
    skills: list[Skill] | None = None
    licenses: list[License] | None = None
    certifications: list[Certification] | None = None
    language_proficiencies: list[Langauge] | None = None

    def get_qualifications_score(self):
        """Returns a 0-100 score based on the details provided"""
        weights = {
            "most_recent_job": 40,
            "education": 25,
            "skills": 20,
            "licenses": 5,
            "certifications": 5,
            "language_proficiencies": 5,
        }

        score = 0
        for attr, weight in weights.items():
            if getattr(self, attr):
                score += weight

        return score


class UpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    phone_number: str | None = None
    qualifications: Qualifications | None = None
    contact_information: ContactInformation | None = None
    demographics: DemographicData | None = None
    job_preferences: JobPreferences | None = None


class CreateUser(UpdateUser):
    first_name: str
    last_name: str
    email: str
    image_url: str | None = None
    phone_number: str | None = None
    auth_id: str
    qualifications: Qualifications = Field(default_factory=Qualifications)
    contact_information: ContactInformation = Field(default_factory=ContactInformation)
    demographics: DemographicData = Field(default_factory=DemographicData)
    job_preferences: JobPreferences = Field(default_factory=JobPreferences)
    profile_is_public: bool = False
    candidate_score: float | None = None


class User(CreateUser, BaseDataModel):
    def get_candidate_score(self):
        return self.qualifications.get_qualifications_score()
