import typing as t
from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base.models import BaseDataModel
from ajb.common.models import GeneralLocation, convert_pay_to_hourly
from ajb.static.enumerations import (
    WorkSettingEnum,
    JobTypeEnum,
    PayType,
)

from .enumerations import (
    RaceEnum,
    GenderEnum,
    LevelOfEducationEnum,
    LanguageProficiencyEnum,
)


class DemographicData(BaseModel):
    birth_year: int | None = None
    race: RaceEnum | None = None
    gender: GenderEnum | None = None
    has_disability: bool | None = None
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


class AlgoliaCandidateConverterHelper:
    def __init__(self, user: User):
        self.user = user

    def get_skills(self):
        return (
            [skill.skill for skill in self.user.qualifications.skills]
            if self.user.qualifications.skills
            else []
        )

    def get_licenses(self):
        return (
            [lisence.license_name for lisence in self.user.qualifications.licenses]
            if self.user.qualifications.licenses
            else []
        )

    def get_certifications(self):
        return (
            [
                certification.certification_name
                for certification in self.user.qualifications.certifications
            ]
            if self.user.qualifications.certifications
            else []
        )

    def get_languages(self):
        return (
            [
                language.language
                for language in self.user.qualifications.language_proficiencies
            ]
            if self.user.qualifications.language_proficiencies
            else []
        )

    def get_most_recent_job_title(self):
        return (
            self.user.qualifications.most_recent_job.job_title
            if self.user.qualifications and self.user.qualifications.most_recent_job
            else None
        )

    def get_most_recent_company(self):
        return (
            self.user.qualifications.most_recent_job.company_name
            if self.user.qualifications and self.user.qualifications.most_recent_job
            else None
        )

    def get_location_geo(self) -> dict[t.Literal["lat", "lng"], float | None] | None:
        return (
            {
                "lat": self.user.contact_information.user_location.lat,
                "lng": self.user.contact_information.user_location.lng,
            }
            if self.user.contact_information
            and self.user.contact_information.user_location
            else None
        )

    def get_has_disability(self):
        return self.user.demographics.has_disability if self.user.demographics else None

    def get_arrest_record(self):
        return self.user.demographics.arrest_record if self.user.demographics else None

    def get_desired_job_title(self):
        return (
            self.user.job_preferences.desired_job_title
            if self.user.job_preferences
            else None
        )

    def get_desired_job_types(self):
        return (
            self.user.job_preferences.desired_job_types
            if self.user.job_preferences
            else None
        )

    def get_desired_schedule(self):
        return (
            self.user.job_preferences.desired_schedule
            if self.user.job_preferences
            else None
        )

    def get_minimum_hourly_desired_pay(self):
        return (
            self.user.job_preferences.desired_pay.get_pay_as_hourly()
            if self.user.job_preferences and self.user.job_preferences.desired_pay
            else None
        )

    def get_willing_to_relocate(self):
        return (
            self.user.job_preferences.willing_to_relocate
            if self.user.job_preferences
            else None
        )

    def get_desired_work_settings(self):
        return (
            self.user.job_preferences.desired_work_settings
            if self.user.job_preferences
            else None
        )

    def get_desired_industries(self):
        return (
            self.user.job_preferences.desired_industries
            if self.user.job_preferences
            else None
        )

    def get_ready_to_start_immediately(self):
        return (
            self.user.job_preferences.ready_to_start_immediately
            if self.user.job_preferences
            else None
        )


class AlgoliaCandidateSearch(BaseModel):
    """This is a flattened version of the user and user details models"""

    user_id: str
    first_name: str
    image_url: str | None
    email: str
    most_recent_job_title: str | None
    most_recent_company: str | None
    skills: list[str]
    licenses: list[str]
    certifications: list[str]
    languages: list[str]
    location_geo: dict[t.Literal["lat", "lng"], float | None] | None = None
    has_disability: bool | None = None
    arrest_record: bool | None = None

    desired_job_title: str | None = None
    desired_job_types: list[JobTypeEnum] | None = None
    desired_schedule: list[JobSchedule] | None = None
    minimum_hourly_desired_pay: float | None = None
    willing_to_relocate: bool | None = None
    desired_work_settings: list[WorkSettingEnum] | None = None
    desired_industries: list[str] | None = None
    ready_to_start_immediately: bool | None = None

    @classmethod
    def convert_from_user(cls, user: User):
        converter_helper = AlgoliaCandidateConverterHelper(user)
        return cls(
            user_id=user.id,
            first_name=user.first_name,
            image_url=user.image_url,
            email=user.email,
            most_recent_job_title=converter_helper.get_most_recent_job_title(),
            most_recent_company=converter_helper.get_most_recent_company(),
            skills=converter_helper.get_skills(),
            licenses=converter_helper.get_licenses(),
            certifications=converter_helper.get_certifications(),
            languages=converter_helper.get_languages(),
            location_geo=converter_helper.get_location_geo(),
            has_disability=converter_helper.get_has_disability(),
            arrest_record=converter_helper.get_arrest_record(),
            desired_job_title=converter_helper.get_desired_job_title(),
            desired_job_types=converter_helper.get_desired_job_types(),
            desired_schedule=converter_helper.get_desired_schedule(),
            minimum_hourly_desired_pay=converter_helper.get_minimum_hourly_desired_pay(),
            willing_to_relocate=converter_helper.get_willing_to_relocate(),
            desired_work_settings=converter_helper.get_desired_work_settings(),
            desired_industries=converter_helper.get_desired_industries(),
            ready_to_start_immediately=converter_helper.get_ready_to_start_immediately(),
        )

    def convert_to_algolia(self):
        output = self.model_dump(mode="json")
        if self.location_geo and self.location_geo["lat"] and self.location_geo["lng"]:
            output["_geoloc"] = {
                "lat": self.location_geo["lat"],
                "lng": self.location_geo["lng"],
            }
        return output
