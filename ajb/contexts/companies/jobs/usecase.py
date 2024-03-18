from ajb.base import BaseUseCase, Collection, RepoFilterParams
from ajb.vendor.arango.models import Filter

from .models import (
    Job,
    CreateJob,
    UserCreateJob,
)


class JobsUseCase(BaseUseCase):
    def create_job(
        self,
        company_id: str,
        job: UserCreateJob
    ) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        job_to_create = CreateJob(**job.model_dump(), company_id=company_id)
        job_to_create.job_score = job.calculate_score()
        created_job = job_repo.create(job_to_create)

        # Update company job count
        company_repo.increment_field(company_id, "total_jobs", 1)
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
        return created_jobs

    def delete_job(self, company_id: str, job_id: str):
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        application_repo = self.get_repository(Collection.APPLICATIONS)
        job_repo.delete(job_id)
        company_repo.decrement_field(company_id, "total_jobs", 1)
        applications = application_repo.query(
            repo_filters=RepoFilterParams(
                filters=[
                    Filter(field="company_id", value=company_id),
                    Filter(field="job_id", value=job_id),
                ]
            )
        )[0]
        application_repo.delete_many([application.id for application in applications])
        return True
