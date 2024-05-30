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
        job_rubric_repo = self.get_repository(
            Collection.JOB_INTERVIEW_RUBRICS, self.request_scope, job_id
        )
        job = self.get_object(Collection.JOBS, job_id)
        job_interview_rubric_to_create = (
            self.ai_job_interview_rubric.generate_job_rubric(job)
        )
        return job_rubric_repo.set_sub_entity(job_interview_rubric_to_create)


# from ajb.vendor.arango.repository import get_arango_db
# from ajb.base import RequestScope
# rs = RequestScope(user_id="ted", db=get_arango_db(), kafka=None)

# usecase = JobInterviewRubricUseCase(rs)
# rubric = usecase.generate_job_interview_rubric("2072644")
