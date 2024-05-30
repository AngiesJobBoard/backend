from ajb.base import Collection, RepositoryRegistry, RequestScope, SingleChildRepository

from .models import CreateInterviewQuestions, InterviewQuestions


class InterviewQuestionsRepository(
    SingleChildRepository[CreateInterviewQuestions, InterviewQuestions]
):
    collection = Collection.INTERVIEW_QUESTIONS
    entity_model = InterviewQuestions

    def __init__(self, request_scope: RequestScope, application_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.APPLICATIONS,
            parent_id=application_id,
        )


RepositoryRegistry.register(InterviewQuestionsRepository)
