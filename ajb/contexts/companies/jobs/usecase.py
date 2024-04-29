from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.applications.models import Application
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

    def delete_job(self, company_id: str, job_id: str):
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        job_repo.delete(job_id)
        company_repo.decrement_field(company_id, "total_jobs", 1)

        # Delete all applications
        application_repo = self.get_repository(Collection.APPLICATIONS)
        all_job_applications: list[Application] = application_repo.get_all(
            company_id=company_id, job_id=job_id
        )
        total_applicant_decrease = len(all_job_applications)
        total_high_match_decrease = len(
            [
                app
                for app in all_job_applications
                if app.application_match_score
                or 0 >= SETTINGS.DEFAULT_HIGH_MATCH_THRESHOLD
            ]
        )
        total_new_application_decrease = len(
            [app for app in all_job_applications if app.application_status is None]
        )
        application_repo.delete_many([app.id for app in all_job_applications])

        # Update company counts
        company_repo = self.get_repository(Collection.COMPANIES)
        company_repo.decrement_field(
            company_id, "total_applicants", total_applicant_decrease
        )
        company_repo.decrement_field(
            company_id, "high_matching_applicants", total_high_match_decrease
        )
        company_repo.decrement_field(
            company_id, "new_applicants", total_new_application_decrease
        )

        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_deletes_job(company_id=company_id, job_id=job_id)
        return True

    def update_job(self, company_id: str, job_id: str, job: UserCreateJob) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job_to_update = CreateJob(**job.model_dump(), company_id=company_id)
        updated_job = job_repo.update(job_id, job_to_update)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_updates_job(company_id=company_id, job_id=job_id)
        return updated_job
