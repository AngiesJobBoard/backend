from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.jobs.job_interview_rubric import (
    JobInterviewRubric,
)
from ajb.vendor.openai.repository import OpenAIRepository


class JobInterviewRubricUseCase(BaseUseCase):

    def __init__(
        self, request_scope: RequestScope, openai: OpenAIRepository | None = None
    ) -> None:
        self.ai_job_interview_class = AIJobInterviewRubricMakerClass(openai)
        self.request_scope = request_scope

    def generate_job_interview_rubric(self, job_id: str) -> JobInterviewRubric:
        job_rubbric_repo = self.get_repository(Collection.JOB_INTERVIEW_RUBRICS)
        job = self.get_object(Collection.Jobs, job_id)
        job_interview_rubric_to_create = self.ai_thingy.generate_job_rubric(job)
        return job_rubbric_repo.create(job_interview_rubric_to_create)
