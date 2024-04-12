from concurrent.futures import ThreadPoolExecutor
from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.applications.models import Application, ScanStatus
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.companies.notifications.usecase import CompanyNotificationUsecase
from ajb.contexts.companies.notifications.models import (
    NotificationType,
    SystemCreateCompanyNotification,
)
from ajb.config.settings import SETTINGS
from ajb.vendor.openai.repository import AsyncOpenAIRepository

from .ai_matching import AIApplicationMatcher, ApplicantMatchScore


class ApplicantMatchUsecase(BaseUseCase):
    def __init__(self, request_scope: RequestScope, openai: AsyncOpenAIRepository):
        self.request_scope = request_scope
        self.openai = openai

    def _get_job(self, job_id: str, job_data: Job | None = None):
        if job_data:
            job = job_data
        else:
            job = self.get_object(Collection.JOBS, job_id)
        return job

    async def get_match(
        self, application: Application, job_data: Job | None = None
    ) -> ApplicantMatchScore:
        return await AIApplicationMatcher(self.openai).get_match_score(
            application, self._get_job(application.job_id, job_data)
        )

    def _handle_high_application_match(self, application: Application, job: Job):
        ApplicationUseCase(self.request_scope).update_application_counts(
            application.company_id,
            application.job_id,
            ApplicationConstants.HIGH_MATCHING_APPLICANTS,
            1,
            True,
        )
        CompanyNotificationUsecase(self.request_scope).create_company_notification(
            application.company_id,
            SystemCreateCompanyNotification(
                company_id=application.company_id,
                notification_type=NotificationType.HIGH_MATCHING_CANDIDATE,
                title=f"High Matching Candidate for {job.position_title}",
                message=f"{application.name} has a high match score for {job.position_title}!",
                application_id=application.id,
                job_id=job.id,
                metadata={
                    "application_name": application.name,
                    "application_email": application.email,
                    "match_score": application.application_match_score,
                    "match_reason": application.application_match_reason,
                    "application_city": (
                        application.user_location.city or ""
                        if application.user_location
                        else ""
                    ),
                    "application_state": (
                        application.user_location.state or ""
                        if application.user_location
                        else ""
                    ),
                    "job_name": job.position_title,
                },
            ),
        )

    async def update_application_with_match_score(
        self, application_id: str, job_data: Job | None = None
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application: Application = application_repo.get(application_id)
        application_repo.update_fields(
            application.id, match_score_status=ScanStatus.STARTED
        )
        job = self._get_job(application.job_id, job_data)
        try:
            match_results = await self.get_match(application, job)
            updated_application = application_repo.update_fields(
                application_id,
                application_match_score=match_results.match_score,
                application_match_reason=match_results.match_reason,
                match_score_status=ScanStatus.COMPLETED,
            )
            if match_results.match_score >= SETTINGS.DEFAULT_HIGH_MATCH_THRESHOLD:
                self._handle_high_application_match(updated_application, job)
            return updated_application
        except Exception as e:
            application_repo.update_fields(
                application_id,
                match_score_status=ScanStatus.FAILED,
                match_score_error_text=str(e),
            )
            raise e

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
