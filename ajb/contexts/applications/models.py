from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field
import pandas as pd

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import (
    DataReducedJob,
    JobNameOnly,
    Location,
    ApplicationQuestion,
    DataReducedCompany,
)
from ajb.vendor.google_maps import get_state_from_lat_long
from ajb.utils import get_datetime_from_string, get_miles_between_lat_long_pairs


class ScanStatus(str, Enum):
    NO_SCAN = "No Scan"
    PENDING = "Pending"
    STARTED = "Started"
    COMPLETED = "Completed"
    FAILED = "Failed"


class DemographicData(BaseModel):
    birth_year: int | None = None
    has_disability: bool | None = None
    arrest_record: bool | None = None


class WorkHistory(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    job_industry: str | None = None
    still_at_job: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Education(BaseModel):
    school_name: str | None = None
    level_of_education: str | None = None
    field_of_study: str | None = None
    still_in_school: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Qualifications(BaseModel):
    most_recent_job: WorkHistory | None = None
    work_history: list[WorkHistory] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    licenses: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    language_proficiencies: list[str] = Field(default_factory=list)


class JobDuration(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    still_at_job: bool | None = None


class AdditionalFilterInformation(BaseModel):
    """
    These are additional attributes that are parsed from an application
    and used to further filter and rank applications
    """

    average_job_duration_in_months: int | None = None
    average_gap_duration_in_months: int | None = None
    total_years_in_workforce: int | None = None
    years_since_first_job: int | None = None
    job_title_list: list[str] | None = None
    miles_between_job_and_applicant: int | None = None
    in_same_state_as_location: bool | None = None
    has_college_degree: bool | None = None


class UserCreatedApplication(BaseModel):
    company_id: str
    job_id: str
    resume_id: str | None = None
    resume_url: str | None = None
    extracted_resume_text: str | None = None
    resume_scan_status: ScanStatus = ScanStatus.NO_SCAN
    resume_scan_error_text: str | None = None
    resume_scan_attempts: int = 0
    match_score_status: ScanStatus = ScanStatus.NO_SCAN
    match_score_error_text: str | None = None
    qualifications: Qualifications = Qualifications()
    additional_filters: AdditionalFilterInformation | None = None
    application_questions: list[ApplicationQuestion] | None = None
    name: str
    email: str
    phone: str | None = None
    user_location: Location | None = None
    external_reference_code: str | None = None

    @classmethod
    def from_csv_record(cls, company_id: str, job_id: str, record: dict):
        return cls(
            company_id=company_id,
            job_id=job_id,
            name=record["name"],
            email=record["email"],
            resume_scan_status=ScanStatus.NO_SCAN,
            match_score_status=ScanStatus.NO_SCAN,
            phone=record.get("phone") if not pd.isnull(record.get("phone")) else None,
            user_location=(
                Location(
                    city=record["city"],
                    state=record["state"],
                    country=record["country"],
                )
                if not pd.isnull(record.get("city"))
                and not pd.isnull(record.get("state"))
                and not pd.isnull(record.get("country"))
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
                    if not pd.isnull(record.get("most_recent_job_title"))
                    and not pd.isnull(record.get("most_recent_company_name"))
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
                    if not pd.isnull(record.get("school_name_1"))
                    and not pd.isnull(record.get("education_level_1"))
                    and not pd.isnull(record.get("field_of_study_1"))
                    else []
                ),
                skills=(
                    record.get("skills", "").split(",")
                    if not pd.isnull(record.get("skills"))
                    else []
                ),
                licenses=(
                    record.get("licenses", "").split(",")
                    if not pd.isnull(record.get("licenses"))
                    else []
                ),
                certifications=(
                    record.get("certifications", "").split(",")
                    if not pd.isnull(record.get("certifications"))
                    else []
                ),
                language_proficiencies=(
                    record.get("language_proficiencies", "").split(",")
                    if not pd.isnull(record.get("language_proficiencies"))
                    and record.get("language_proficiencies")
                    else []
                ),
            ),
        )


class UpdateApplication(BaseModel):
    resume_id: str | None = None
    extracted_resume_text: str | None = None
    resume_scan_status: ScanStatus | None = None
    resume_scan_error_test: str | None = None
    match_score_status: ScanStatus | None = None
    match_score_error_text: str | None = None
    qualifications: Qualifications | None = None
    additional_filters: AdditionalFilterInformation | None = None
    application_questions: list[ApplicationQuestion] | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    user_location: Location | None = None
    resume_url: str | None = None
    external_reference_code: str | None = None


class CreateApplicationStatusUpdate(BaseModel):
    application_status: str
    update_reason: str | None = None


class ApplicationStatusRecord(CreateApplicationStatusUpdate):
    updated_by_user_id: str
    update_made_by_admin: bool


class CreateApplication(UserCreatedApplication):
    application_status: str | None = None
    application_match_score: int | None = None
    application_match_reason: str = ""

    recruiter_tags: list[str] = Field(default_factory=list)


class Application(CreateApplication, BaseDataModel):

    def _get_job_duration_tuples(self) -> list[JobDuration]:
        duration_tuples = []
        if self.qualifications and self.qualifications.work_history:
            for work_history in self.qualifications.work_history:
                if (
                    work_history.start_date
                    and isinstance(work_history.start_date, datetime)
                    and work_history.end_date
                    and isinstance(work_history.end_date, datetime)
                ):
                    duration_tuple = JobDuration(
                        start_date=work_history.start_date,
                        end_date=work_history.end_date,
                        still_at_job=work_history.still_at_job or False,
                    )
                    duration_tuples.append(duration_tuple)
        sorted_duration_tuples = sorted(duration_tuples, key=lambda x: x.start_date)
        return sorted_duration_tuples

    def get_average_job_duration_in_months(self):
        job_duration_tuples = self._get_job_duration_tuples()
        if not job_duration_tuples:
            return None

        durations = []
        for job_duration in job_duration_tuples:
            if job_duration.start_date and job_duration.end_date:
                duration = relativedelta(job_duration.end_date, job_duration.start_date)
                durations.append(
                    duration.years * 12 + duration.months + duration.days / 30.0
                )
        if not durations:
            return 0
        return int(sum(durations) / len(durations))

    def get_average_gap_duration_in_months(self):
        job_duration_tuples = self._get_job_duration_tuples()
        if not job_duration_tuples:
            return None

        gaps = []
        for i in range(len(job_duration_tuples) - 1):
            if job_duration_tuples[i].end_date:
                gap = relativedelta(
                    job_duration_tuples[i + 1].start_date,
                    job_duration_tuples[i].end_date,
                )
                gaps.append(gap.years * 12 + gap.months + gap.days / 30.0)
        if not gaps:
            return 0
        return int(sum(gaps) / len(gaps))

    def get_total_years_in_workforce(self) -> int | None:
        # Sum all time worked in months and divide by 12
        job_duration_tuples = self._get_job_duration_tuples()
        if not job_duration_tuples:
            return None
        total_months = 0
        for job_duration in job_duration_tuples:
            if job_duration.start_date and job_duration.end_date:
                duration = relativedelta(job_duration.end_date, job_duration.start_date)
                total_months += (
                    duration.years * 12 + duration.months + duration.days / 30.0
                )
        return int(total_months / 12)

    def get_years_since_first_job(self) -> int | None:
        job_duration_tuples = self._get_job_duration_tuples()
        if not job_duration_tuples:
            return None
        total_days = 0
        for job_duration in job_duration_tuples:
            if job_duration.start_date and job_duration.end_date:
                total_days += (job_duration.end_date - job_duration.start_date).days
        return int(total_days / 365)

    def has_college_degree(self):
        """
        Loops through education array looking for any reference to a college degree
        """
        if not self.qualifications or not self.qualifications.education:
            return False

        for education in self.qualifications.education:
            if not education.level_of_education:
                continue
            if any(
                word in education.level_of_education.lower()
                for word in [
                    "bachelor",
                    "master",
                    "doctor",
                    "phd",
                    "college",
                    "university",
                ]
            ):
                return True
        return False

    def get_job_title_list(self) -> list[str]:
        all_job_titles = []
        if self.qualifications and self.qualifications.most_recent_job:
            all_job_titles.append(self.qualifications.most_recent_job.job_title)

        if self.qualifications and self.qualifications.work_history:
            all_job_titles.extend(
                [
                    work_history.job_title
                    for work_history in self.qualifications.work_history
                ]
            )

        return list(set([job_title for job_title in all_job_titles if job_title]))

    def get_miles_from_job_location(
        self, job_lat: float | None, job_lon: float | None
    ) -> int | None:
        if (
            job_lat is not None
            and job_lon is not None
            and self.user_location is not None
            and self.user_location.lat is not None
            and self.user_location.lng is not None
        ):
            return get_miles_between_lat_long_pairs(
                self.user_location.lat, self.user_location.lng, job_lat, job_lon
            )
        return None

    def _convert_work_history_to_datetime(self):
        if not self.qualifications or not self.qualifications.most_recent_job:
            return

        if isinstance(self.qualifications.most_recent_job.start_date, str):
            self.qualifications.most_recent_job.start_date = get_datetime_from_string(
                self.qualifications.most_recent_job.start_date
            )

        if isinstance(self.qualifications.most_recent_job.end_date, str):
            self.qualifications.most_recent_job.end_date = get_datetime_from_string(
                self.qualifications.most_recent_job.end_date
            )

        if not self.qualifications.work_history:
            return

        for work_history in self.qualifications.work_history:
            if isinstance(work_history.start_date, str):
                work_history.start_date = get_datetime_from_string(
                    work_history.start_date
                )

            if isinstance(work_history.end_date, str):
                work_history.end_date = get_datetime_from_string(work_history.end_date)

    def applicant_is_in_same_state_as_job(
        self, job_lat: float | None, job_lon: float | None
    ) -> bool:
        if (
            not self.user_location
            or self.user_location.lat is None
            or self.user_location.lng is None
            or job_lat is None
            or job_lon is None
        ):
            return False

        job_state = get_state_from_lat_long(job_lat, job_lon)
        user_state = get_state_from_lat_long(
            self.user_location.lat, self.user_location.lng
        )
        return job_state == user_state

    def extract_filter_information(
        self, job_lat: float | None = None, job_lon: float | None = None
    ):
        self._convert_work_history_to_datetime()
        self.additional_filters = AdditionalFilterInformation(
            average_job_duration_in_months=self.get_average_job_duration_in_months(),
            average_gap_duration_in_months=self.get_average_gap_duration_in_months(),
            total_years_in_workforce=self.get_total_years_in_workforce(),
            years_since_first_job=self.get_years_since_first_job(),
            job_title_list=self.get_job_title_list(),
            miles_between_job_and_applicant=self.get_miles_from_job_location(
                job_lat, job_lon
            ),
            in_same_state_as_location=self.applicant_is_in_same_state_as_job(
                job_lat, job_lon
            ),
            has_college_degree=self.has_college_degree(),
        )


@dataclass
class PaginatedApplications(PaginatedResponse[Application]):
    data: list[Application]


class ApplicantAndJob(BaseDataModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    application_status: str | None = None
    application_match_score: int | None
    application_match_reason: str
    job: JobNameOnly | None


class CompanyApplicationView(Application):
    job: DataReducedJob
    other_applications: list[ApplicantAndJob] = Field(default_factory=list)


class AdminApplicationView(CompanyApplicationView):
    company: DataReducedCompany


@dataclass
class PaginatedCompanyApplicationView(PaginatedResponse[CompanyApplicationView]):
    data: list[CompanyApplicationView]


@dataclass
class PaginatedAdminApplicationView(PaginatedResponse[AdminApplicationView]):
    data: list[AdminApplicationView]


class DataReducedQualifications(BaseModel):
    most_recent_job: WorkHistory | None = None
    skills: list[str] | None = None


class DataReducedApplication(BaseDataModel):
    application_status: str | None = None
    application_match_score: int | None
    application_match_reason: str

    recruiter_tags: list[str] = Field(default_factory=list)

    resume_id: str | None = None
    resume_scan_status: ScanStatus | None = None
    resume_scan_error_test: str | None = None
    match_score_status: ScanStatus | None = None
    match_score_error_text: str | None = None

    qualifications: DataReducedQualifications | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    user_location: Location | None = None
    resume_url: str | None = None
    external_reference_code: str | None = None

    job_id: str
    company_id: str
    job: JobNameOnly | None = None


@dataclass
class PaginatedDataReducedApplication(PaginatedResponse[DataReducedApplication]):
    data: list[DataReducedApplication]
