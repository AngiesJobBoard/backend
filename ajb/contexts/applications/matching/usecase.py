from concurrent.futures import ThreadPoolExecutor
from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.applications.models import Application, ScanStatus
from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.openai.repository import AsyncOpenAIRepository

from .ai_matching import AIApplicationMatcher, ApplicantMatchScore


class ApplicantMatchUsecase(BaseUseCase):
    def __init__(self, request_scope: RequestScope, openai: AsyncOpenAIRepository):
        self.request_scope = request_scope
        self.openai = openai

    async def get_match(
        self, application: Application, job_data: Job | None = None
    ) -> ApplicantMatchScore:
        if job_data:
            job = job_data
        else:
            job = self.get_object(Collection.JOBS, application.job_id)
        return await AIApplicationMatcher(self.openai).get_match_score(application, job)

    async def update_application_with_match_score(
        self, application_id: str, job_data: Job | None = None
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application: Application = application_repo.get(application_id)
        application_repo.update_fields(
            application.id, match_score_status=ScanStatus.STARTED
        )
        try:
            match_results = await self.get_match(application, job_data)
        except Exception as e:
            application_repo.update_fields(
                application_id,
                match_score_status=ScanStatus.FAILED,
                match_score_error_text=str(e),
            )
            raise e
        return application_repo.update_fields(
            application_id,
            application_match_score=match_results.match_score,
            application_match_reason=match_results.match_reason,
            match_score_status=ScanStatus.COMPLETED,
        )

    def update_many_applications_with_match_scores(
        self, application_id_list: list[str], job_id: str
    ):
        job = self.get_object(Collection.JOBS, job_id)
        with ThreadPoolExecutor(max_workers=5) as executor:
            for application_id in application_id_list:
                executor.submit(
                    self.update_application_with_match_score, application_id, job
                )
        return True
