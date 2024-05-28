from ajb.base import Collection, RepositoryRegistry, RequestScope, SingleChildRepository

from .models import CreateJobInterviewRubric, JobInterviewRubric


class JobInterviewRubricRepository(
    SingleChildRepository[CreateJobInterviewRubric, JobInterviewRubric]
):
    collection = Collection.JOB_INTERVIEW_RUBRICS
    entity_model = JobInterviewRubric

    def __init__(self, request_scope: RequestScope, job_id: str):
        super().__init__(
            request_scope, parent_collection=Collection.JOBS, parent_id=job_id
        )


RepositoryRegistry.register(JobInterviewRubricRepository)
