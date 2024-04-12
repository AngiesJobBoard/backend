from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.companies.models import Company
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.companies.email_ingress_webhooks.repository import (
    CompanyEmailIngressRepository,
)
from ajb.contexts.companies.email_ingress_webhooks.models import (
    CreateCompanyEmailIngress,
    EmailIngressType,
)
from ajb.contexts.companies.jobs.job_score.ai_job_score import AIJobScore
from ajb.vendor.openai.repository import OpenAIRepository

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

    def _update_job_with_score(self, job: CreateJob) -> CreateJob:
        job_score = AIJobScore(self.openai).get_job_score(job)
        job.job_score = job_score.job_score
        job.job_score_reason = job_score.job_score_reason
        return job

    def create_job(
        self,
        company_id: str,
        job: UserCreateJob,
        openai: OpenAIRepository | None = None,
    ) -> Job:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        company_repo = self.get_repository(Collection.COMPANIES)
        job_to_create = CreateJob(**job.model_dump(), company_id=company_id)
        job_with_score = self._update_job_with_score(job_to_create)

        # Create the job
        created_job: Job = job_repo.create(job_with_score)

        # Update company job count
        company_repo.increment_field(company_id, "total_jobs", 1)

        # Get the company object to check default ingress settings
        company: Company = self.get_object(Collection.COMPANIES, company_id)

        # Create email ingress record
        CompanyEmailIngressRepository(self.request_scope).create(
            CreateCompanyEmailIngress.generate(
                company_id,
                EmailIngressType.CREATE_APPLICATION,
                created_job.id,
                company.settings.enable_all_email_ingress,
            )
        )

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
            job_with_score = self._update_job_with_score(job_to_create)
            jobs_to_create.append(job_with_score)
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
        job_with_score = self._update_job_with_score(job_to_update)
        updated_job = job_repo.update(job_id, job_with_score)

        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_updates_job(job_id=job_id)
        return updated_job
