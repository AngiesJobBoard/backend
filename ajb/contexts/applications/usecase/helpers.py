from ajb.base import BaseUseCase
from ajb.base.schema import Collection
from ajb.common.models import ApplicationQuestion
from ajb.contexts.companies.jobs.models import Job


class ApplicationHelpersUseCase(BaseUseCase):
    def get_job_questions(self, job_id: str) -> list[ApplicationQuestion]:
        job: Job = self.get_object(Collection.JOBS, job_id)
        if not job.application_questions_as_strings:
            return []
        return [
            ApplicationQuestion(question=question)
            for question in job.application_questions_as_strings
        ]

    def update_application_counts(
        self,
        company_id: str,
        job_id: str,
        field: str,
        count_change: int,
        is_increase: bool,
    ) -> None:
        company_repo = self.get_repository(Collection.COMPANIES)
        job_repo = self.get_repository(
            Collection.JOBS, self.request_scope, parent_id=company_id
        )
        if is_increase:
            company_repo.increment_field(company_id, field, count_change)
            job_repo.increment_field(job_id, field, count_change)
            return
        company_repo.decrement_field(company_id, field, count_change)
        job_repo.decrement_field(job_id, field, count_change)
