from ajb.base import BaseUseCase
from ajb.base.events import SourceServices
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.models import CreateApplication, Application, ScanStatus
from ajb.contexts.resumes.models import UserCreateResume, Resume
from ajb.contexts.resumes.usecase import ResumeUseCase


from .create_application import CreateApplicationResolver


class CreateApplicationFromResumeResolver(BaseUseCase):
    def _build_application_from_resume(self, resume: Resume) -> CreateApplication:
        return CreateApplication(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            resume_scan_status=ScanStatus.PENDING,
            match_score_status=ScanStatus.PENDING,
        )

    def _combine_additional_data(
        self,
        partial_application: CreateApplication,
        additional_partial_data: CreateApplication | None,
    ) -> CreateApplication:
        if not additional_partial_data:
            return partial_application

        partial_application_dict = partial_application.model_dump()
        additional_partial_data_dict = additional_partial_data.model_dump()
        partial_application_dict.update(additional_partial_data_dict)
        return CreateApplication(**partial_application_dict)

    def _create_application(
        self, partial_application: CreateApplication
    ) -> Application:
        return CreateApplicationResolver(self.request_scope).create_application(
            partial_application.company_id,
            partial_application.job_id,
            partial_application,
            produce_submission_event=False,
        )

    def _produce_resume_upload_event(
        self, resume: Resume, created_application: Application
    ) -> None:
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
        )

    def _format_application_data(
        self, resume: Resume, additional_partial_data: CreateApplication | None = None
    ):
        partial_application = self._build_application_from_resume(resume)
        partial_application = self._combine_additional_data(
            partial_application, additional_partial_data
        )
        return partial_application

    def create_application_from_resume(
        self,
        data: UserCreateResume,
        additional_partial_data: CreateApplication | None = None,
    ) -> Application:
        resume = ResumeUseCase(self.request_scope).create_resume(data)
        application_data = self._format_application_data(
            resume, additional_partial_data
        )
        created_application = self._create_application(application_data)
        self._produce_resume_upload_event(resume, created_application)
        return created_application
