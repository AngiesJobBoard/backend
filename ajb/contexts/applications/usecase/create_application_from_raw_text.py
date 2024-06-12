from ajb.base import BaseUseCase
from ajb.base.events import SourceServices
from ajb.contexts.applications.models import CreateApplication, ScanStatus, Application
from ajb.contexts.applications.extract_data.ai_extractor import (
    SyncronousAIResumeExtractor,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.events import ApplicationEventProducer

from .create_application import CreateApplicationResolver
from .helpers import ApplicationHelpersUseCase


class CreateApplicationFromRawTextResolver(BaseUseCase):
    def _get_application_with_questions(
        self, company_id: str, job_id: str, raw_text: str
    ) -> CreateApplication:
        partial_application = CreateApplication(
            company_id=company_id,
            job_id=job_id,
            match_score_status=ScanStatus.STARTED,
            extracted_resume_text=raw_text,
        )
        partial_application.application_questions = ApplicationHelpersUseCase(
            self.request_scope
        ).get_job_questions(job_id)
        return partial_application

    def _create_application(
        self, company_id: str, job_id: str, raw_text: str
    ) -> Application:
        application_data = self._get_application_with_questions(
            company_id, job_id, raw_text
        )
        return CreateApplicationResolver(self.request_scope).create_application(
            company_id, job_id, application_data, produce_submission_event=False
        )

    def _update_application_with_resume_information(
        self, application: Application
    ) -> Application:
        application_repo = ApplicationRepository(self.request_scope)
        resume_information = (
            SyncronousAIResumeExtractor().get_candidate_profile_from_resume_text(
                str(application.extracted_resume_text)
            )
        )
        return application_repo.update_application_with_parsed_information(
            application_id=application.id,
            resume_information=resume_information,  # type: ignore
        )

    def _produce_event(self, application: Application) -> None:
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_gets_match_score(
            company_id=application.company_id,
            job_id=application.job_id,
            application_id=application.id,
        )

    def application_is_created_from_raw_text(
        self, company_id: str, job_id: str, raw_text: str
    ) -> Application:
        created_application = self._create_application(company_id, job_id, raw_text)
        updated_application = self._update_application_with_resume_information(
            created_application
        )
        self._produce_event(updated_application)
        return updated_application
