from ajb.base.events import SourceServices
from ajb.base.schema import Collection
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.extract_data.ai_extractor import (
    SyncronousAIResumeExtractor,
)
from ajb.contexts.applications.models import Application, CreateApplication, ScanStatus
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.resumes.usecase import ResumeUseCase


class ApplicationCreationUseCase:
    def __init__(self, main):
        self.main = main

    def create_application(
        self,
        company_id: str,
        job_id: str,
        partial_application: CreateApplication,
        produce_submission_event: bool = True,
    ) -> Application:
        application_repo = self.main.get_repository(Collection.APPLICATIONS)
        partial_application.application_questions = (
            self.main.helpers._get_job_questions(job_id)
        )
        created_application: Application = application_repo.create(partial_application)
        self.main.updates.update_application_counts(
            company_id, job_id, ApplicationConstants.TOTAL_APPLICANTS, 1, True
        )
        self.main.updates.update_application_counts(
            company_id, job_id, ApplicationConstants.NEW_APPLICANTS, 1, True
        )

        if produce_submission_event:
            ApplicationEventProducer(
                self.main.request_scope, source_service=SourceServices.API
            ).application_is_submitted(
                created_application.company_id,
                created_application.job_id,
                created_application.id,
            )
        return created_application

    def create_many_applications(
        self,
        company_id: str,
        job_id: str,
        partial_applications: list[CreateApplication],
        produce_submission_event: bool = True,
    ) -> list[str]:
        application_repo = self.main.get_repository(Collection.APPLICATIONS)
        job_questions = self.main.helpers._get_job_questions(job_id)
        candidates_with_job_questions = []
        for candidate in partial_applications:
            candidate.application_questions = job_questions
            candidates_with_job_questions.append(candidate)
        created_applications = application_repo.create_many(
            candidates_with_job_questions
        )
        self.main.updates.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.TOTAL_APPLICANTS,
            len(created_applications),
            True,
        )
        self.main.updates.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.NEW_APPLICANTS,
            len(created_applications),
            True,
        )

        if produce_submission_event:
            event_producer = ApplicationEventProducer(
                self.main.request_scope, SourceServices.API
            )
            for application in created_applications:
                event_producer.application_is_submitted(company_id, job_id, application)
        return created_applications

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        return self.main.creation.create_many_applications(
            company_id, job_id, partial_candidates
        )

    def create_application_from_resume(
        self,
        data: UserCreateResume,
        additional_partial_data: CreateApplication | None = None,
    ) -> Application:
        # Create an application for this resume
        resume = ResumeUseCase(self.main.request_scope).create_resume(data)
        partial_application = CreateApplication(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            name="-",
            email="-",
            resume_scan_status=ScanStatus.PENDING,
            match_score_status=ScanStatus.PENDING,
        )
        if additional_partial_data:
            partial_application_dict = partial_application.model_dump()
            additional_partial_data_dict = additional_partial_data.model_dump()
            partial_application_dict.update(additional_partial_data_dict)
            partial_application = CreateApplication(**partial_application_dict)
        created_application = self.main.creation.create_application(
            resume.company_id, resume.job_id, partial_application, False
        )
        # Create kafka event for parsing the resume
        ApplicationEventProducer(
            self.main.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
            parse_resume=True,
        )
        return created_application

    def application_is_created_from_raw_text(
        self, company_id: str, job_id: str, raw_text: str
    ):
        partial_application = CreateApplication(
            company_id=company_id,
            job_id=job_id,
            name="-",
            email="-",
            match_score_status=ScanStatus.STARTED,
            extracted_resume_text=raw_text,
        )
        partial_application.application_questions = (
            self.main.helpers._get_job_questions(job_id)
        )
        created_application = self.main.creation.create_application(
            company_id, job_id, partial_application, False
        )
        resume_information = (
            SyncronousAIResumeExtractor().get_candidate_profile_from_resume_text(
                raw_text
            )
        )
        application_repo: ApplicationRepository = self.main.get_repository(Collection.APPLICATIONS)  # type: ignore
        application_repo.update_application_with_parsed_information(
            application_id=created_application.id,
            resume_url=created_application.resume_url,
            raw_resume_text=raw_text,
            resume_information=resume_information,  # type: ignore
        )

        # Create kafka event for handling the match
        ApplicationEventProducer(
            self.main.request_scope, source_service=SourceServices.API
        ).application_is_submitted(
            company_id=company_id,
            job_id=job_id,
            application_id=created_application.id,
        )
        return created_application
