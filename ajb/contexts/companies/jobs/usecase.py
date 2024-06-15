from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.applications.models import Application
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.billing.validate_usage import BillingValidateUsageUseCase, UsageType
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.config.settings import SETTINGS

from .models import (
    Job,
    CreateJob,
    UserCreateJob,
)


class JobsUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        openai: OpenAIRepository | None = None,
    ):
        self.request_scope = request_scope
        self.openai = openai or OpenAIRepository()

    def create_job(
        self,
        company_id: str,
        job: UserCreateJob,
    ) -> Job:
        BillingValidateUsageUseCase(self.request_scope).validate_usage(
            company_id, UsageType.TOTAL_JOBS
        )
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        created_job: Job = job_repo.create(
            CreateJob(**job.model_dump(), company_id=company_id)
        )

        # Create event
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_creates_job(company_id=company_id, job_id=created_job.id)
        return created_job

    def create_many_jobs(self, company_id: str, jobs: list[UserCreateJob]) -> list[str]:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        jobs_to_create = []
        for job in jobs:
            jobs_to_create.append(CreateJob(**job.model_dump(), company_id=company_id))
        created_jobs = job_repo.create_many(jobs_to_create)

        # Update company job count
        company_repo = self.get_repository(Collection.COMPANIES)
        company_repo.increment_field(company_id, "total_jobs", len(jobs))

        # Create even for each job
        event_producer = CompanyEventProducer(self.request_scope, SourceServices.API)
        for created_job_id in created_jobs:
            event_producer.company_creates_job(
                company_id=company_id, job_id=created_job_id
            )
        return created_jobs

    def update_job(self, company_id: str, job_id: str, job: UserCreateJob) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job_to_update = CreateJob(**job.model_dump(), company_id=company_id)
        updated_job = job_repo.update(job_id, job_to_update)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_updates_job(company_id=company_id, job_id=job_id)
        return updated_job

    def _get_job_application_counts(
        self, company_id: str, job_id: str
    ) -> tuple[int, int, int]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        all_job_applications: list[Application] = application_repo.get_all(
            company_id=company_id, job_id=job_id
        )
        total_applicants = len(all_job_applications)
        total_high_match = len(
            [
                app
                for app in all_job_applications
                if app.application_match_score
                and 0 >= SETTINGS.DEFAULT_HIGH_MATCH_THRESHOLD
            ]
        )
        total_new = len(
            [app for app in all_job_applications if app.application_status is None]
        )
        return total_applicants, total_high_match, total_new

    def _update_company_counts(self, company_id: str):
        # Prepare repos
        application_repo = CompanyApplicationRepository(self.request_scope)
        company_repo = CompanyRepository(self.request_scope)
        job_repo = JobRepository(self.request_scope, company_id)

        # Count applications
        new_count = 0
        total_count = 0
        high_match_count = 0

        applications = application_repo.get_all(company_id=company_id)
        for application in applications:
            # For each application, find it's associated job.
            application_job = job_repo.get(application.job_id)
            if application_job.active:
                # The job is active, so we will count it
                total_count += 1
                if application.application_status == None:
                    # This application doesn't have a status yet, so it's a new one
                    new_count += 1
                if (
                    isinstance(application.application_match_score, int)
                    and application.application_match_score >= 70
                ):
                    # This is a high matching application
                    high_match_count += 1

        # Count jobs
        total_jobs = 0

        jobs = job_repo.get_all()
        for job in jobs:
            if job.active:
                total_jobs += 1

        # Update counters in company repository
        company_repo.update_fields(
            id=company_id,
            total_applicants=total_count,
            new_applicants=new_count,
            high_matching_applicants=high_match_count,
            total_jobs=total_jobs,
        )

    def update_job_active_status(
        self, company_id: str, job_id: str, active: bool
    ) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        original_job: Job = job_repo.get(job_id)
        if original_job.active == active:
            # Do nothing if the job is already in the desired state
            return original_job

        # Update the job and it's counts
        updated_job = job_repo.update_fields(job_id, active=active)
        self._update_company_counts(company_id)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_updates_job(company_id=company_id, job_id=job_id)
        return updated_job
