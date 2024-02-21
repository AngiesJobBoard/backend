from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field
import pandas as pd

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedJob, GeneralLocation

from .enumerations import ApplicationStatus


class ResumeScanStatus(str, Enum):
    PENDING = "Pending"
    STARTED = "Started"
    COMPLETED = "Completed"
    FAILED = "Failed"


class DemographicData(BaseModel):
    birth_year: int | None = None
    has_disability: bool | None = None
    arrest_record: bool | None = None


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


class Qualifications(BaseModel):
    most_recent_job: WorkHistory | None = None
    work_history: list[WorkHistory] | None = None
    education: list[Education] | None = None
    skills: list[str] | None = None
    licenses: list[str] | None = None
    certifications: list[str] | None = None
    language_proficiencies: list[str] | None = None

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


class UserCreatedApplication(BaseModel):
    company_id: str
    job_id: str
    resume_id: str | None = None
    extracted_resume_text: str | None = None
    resume_scan_status: ResumeScanStatus = ResumeScanStatus.PENDING
    resume_scan_error_test: str | None = None
    qualifications: Qualifications | None = None
    name: str
    email: str
    phone: str | None = None
    user_location: GeneralLocation | None = None

    @classmethod
    def from_csv_record(cls, company_id: str, job_id: str, record: dict):
        return cls(
            company_id=company_id,
            job_id=job_id,
            name=record["name"],
            email=record["email"],
            phone=record.get("phone") if not pd.isnull(record.get("phone")) else None,
            user_location=(
                GeneralLocation(
                    city=record["city"],
                    state=record["state"],
                    country=record["country"],
                )
                if not pd.isnull(record.get("city")) and not pd.isnull(record.get("state")) and not pd.isnull(record.get("country"))
                else None
            ),
            qualifications=Qualifications(
                most_recent_job=(
                    WorkHistory(
                        job_title=record["most_recent_job_title"],
                        company_name=record["most_recent_company_name"],
                        start_date=record.get("most_recent_start_date"),
                        end_date=record.get("most_recent_end_date"),
                    )
                    if not pd.isnull(record.get("most_recent_job_title")) and not pd.isnull(record.get("most_recent_company_name"))
                    else None
                ),
                work_history=[],
                education=(
                    [
                        Education(
                            school_name=record["school_name_1"],
                            level_of_education=record["education_level_1"],
                            field_of_study=record["field_of_study_1"],
                            start_date=record.get("education_start_date_1"),
                            end_date=record.get("education_end_date_1"),
                        ),
                    ]
                    if not pd.isnull(record.get("school_name_1")) and not pd.isnull(record.get("education_level_1")) and not pd.isnull(record.get("field_of_study_1"))
                    else None
                ),
                skills=(
                    record.get("skills", "").split(",")
                    if not pd.isnull(record.get("skills"))
                    else None
                ),
                licenses=(
                    record.get("licenses", "").split(",")
                    if not pd.isnull(record.get("licenses"))
                    else None
                ),
                certifications=(
                    record.get("certifications", "").split(",")
                    if not pd.isnull(record.get("certifications"))
                    else None
                ),
                language_proficiencies=(
                    record.get("language_proficiencies", "").split(",")
                    if not pd.isnull(record.get("language_proficiencies")) and record.get("language_proficiencies")
                    else None
                ),
            ),
        )


class UpdateApplication(BaseModel):
    resume_id: str | None = None
    extracted_resume_text: str | None = None
    resume_scan_status: ResumeScanStatus | None = None
    resume_scan_error_test: str | None = None
    qualifications: Qualifications | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    user_location: GeneralLocation | None = None


class UserCreateRecruiterNote(BaseModel):
    note: str


class CreateRecruiterNote(UserCreateRecruiterNote):
    user_id: str


class RecruiterNote(CreateRecruiterNote):
    id: str
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime | None = None


class CreateApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    update_reason: str


class ApplicationStatusRecord(CreateApplicationStatusUpdate):
    updated_by_user_id: str
    update_made_by_admin: bool


class CreateApplication(UserCreatedApplication):
    application_status: ApplicationStatus = ApplicationStatus.CREATED_BY_COMPANY

    application_status_history: list[ApplicationStatusRecord] = Field(
        default_factory=list
    )
    application_is_shortlisted: bool = False
    application_match_score: int | None = None
    application_match_reason: str = ""

    recruiter_tags: list[str] = Field(default_factory=list)
    recruiter_notes: dict[str, RecruiterNote] = Field(default_factory=dict)


class Application(CreateApplication, BaseDataModel): ...


@dataclass
class PaginatedApplications(PaginatedResponse[Application]):
    data: list[Application]


class CompanyApplicationView(Application):
    job: DataReducedJob


@dataclass
class PaginatedCompanyApplicationView(PaginatedResponse[CompanyApplicationView]):
    data: list[CompanyApplicationView]
