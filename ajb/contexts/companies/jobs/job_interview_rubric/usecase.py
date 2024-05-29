from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.jobs.job_interview_rubric.ai_job_interview_rubric import (
    AIJobInterviewRubric,
)
from ajb.contexts.companies.jobs.job_interview_rubric.models import JobInterviewRubric
from ajb.vendor.openai.repository import OpenAIRepository


class JobInterviewRubricUseCase(BaseUseCase):

    def __init__(
        self, request_scope: RequestScope, openai: OpenAIRepository | None = None
    ) -> None:
        self.ai_job_interview_rubric = AIJobInterviewRubric(openai)
        self.request_scope = request_scope

    def generate_job_interview_rubric(self, job_id: str) -> JobInterviewRubric:
        job_rubric_repo = self.get_repository(Collection.JOB_INTERVIEW_RUBRICS)
        job = self.get_object(Collection.Jobs, job_id)
        job_interview_rubric_to_create = (
            self.ai_job_interview_rubric.generate_job_rubric(job)
        )
        return job_rubric_repo.create(job_interview_rubric_to_create)
