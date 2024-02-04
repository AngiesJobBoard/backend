from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.applications.models import Application
from ajb.vendor.openai.repository import OpenAIRepository

from .ai_matching import AIApplicationMatcher, ApplicantMatchScore


class ApplicantMatchUsecase(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, openai: OpenAIRepository | None = None
    ):
        self.request_scope = request_scope
        self.openai = openai or OpenAIRepository()

    def get_match(self, application: Application) -> ApplicantMatchScore:
        user = self.get_object(Collection.USERS, application.user_id)
        job = self.get_object(Collection.JOBS, application.job_id)
        return AIApplicationMatcher(self.openai).get_match_score(user, job)

    def update_application_with_match_score(
        self, application: Application
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        match_results = self.get_match(application)
        return application_repo.update_fields(
            application.id,
            application_match_score=match_results.match_score,
            application_match_reason=match_results.match_reason,
        )
