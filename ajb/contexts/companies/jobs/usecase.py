from ajb.base import BaseUseCase, Collection, RepoFilterParams
from ajb.base.events import SourceServices
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.arango.models import Filter

from .models import (
    Job,
    CreateJob,
    UserCreateJob,
)


class JobsUseCase(BaseUseCase):
    def create_job(self, company_id: str, job: UserCreateJob) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        job_to_create = CreateJob(**job.model_dump(), company_id=company_id)
        job_to_create.job_score = job.calculate_score()
        created_job: Job = job_repo.create(job_to_create)

        # Update company  job count
        company_repo.increment_field(company_id, "total_jobs", 1)

        # Create event
        self.request_scope.company_id = company_id
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_creates_job(job_id=created_job.id)
        return created_job

    def create_many_jobs(self, company_id: str, jobs: list[UserCreateJob]) -> list[str]:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        jobs_to_create = []
        for job in jobs:
            job_to_create = CreateJob(**job.model_dump(), company_id=company_id)
            job_to_create.job_score = job.calculate_score()
            jobs_to_create.append(job_to_create)
        created_jobs = job_repo.create_many(jobs_to_create)

        # Update company job count
        company_repo = self.get_repository(Collection.COMPANIES)
        company_repo.increment_field(company_id, "total_jobs", len(jobs))

        # Create even for each job
        self.request_scope.company_id = company_id
        event_producer = CompanyEventProducer(self.request_scope, SourceServices.API)
        for created_job_id in created_jobs:
            event_producer.company_creates_job(job_id=created_job_id)
        return created_jobs

    def delete_job(self, company_id: str, job_id: str):
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        job_repo.delete(job_id)
        company_repo.decrement_field(company_id, "total_jobs", 1)         
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_deletes_job(job_id=job_id)
        return True

    def update_job(self, company_id: str, job_id: str, job: UserCreateJob) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job_to_update = CreateJob(**job.model_dump(), company_id=company_id)
        job_to_update.job_score = job.calculate_score()
        updated_job = job_repo.update(job_id, job_to_update)

        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_updates_job(job_id=job_id)
        return updated_job
