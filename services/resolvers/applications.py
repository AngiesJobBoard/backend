"""
This module contains the asyncronous event handlers for the company context.
These are triggered when a company event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

import asyncio

from ajb.base import RequestScope
from ajb.base.events import BaseKafkaMessage, SourceServices
from ajb.contexts.applications.events import (
    ResumeAndApplication,
    ApplicantAndCompany,
    IngressEvent
)
from ajb.contexts.applications.models import (
    ScanStatus,
    UpdateApplication,
    Application,
)
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.extract_data.usecase import ResumeExtractorUseCase
from ajb.contexts.applications.application_questions.usecase import (
    ApplicantQuestionsUsecase,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.webhooks.egress.applicants.usecase import (
    CompanyApplicantsWebhookEgress,
)
from ajb.contexts.billing.usecase import (
    CompanyBillingUsecase,
    UsageType,
)
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.openai.repository import OpenAIRepository, AsyncOpenAIRepository
from ajb.exceptions import RepositoryNotProvided
from transformers.router import route_transformer_request


class CouldNotParseResumeText(Exception):
    pass


class MissingAsyncOpenAIRepository(RepositoryNotProvided):
    def __init__(self):
        super().__init__("Async OpenAI Repository")


class ApplicationEventsResolver:
    def __init__(
        self,
        message: BaseKafkaMessage,
        request_scope: RequestScope,
        sendgrid: SendgridRepository | None = None,
        openai: OpenAIRepository | None = None,
        async_openai: AsyncOpenAIRepository | None = None,
    ):
        self.message = message
        self.request_scope = request_scope
        self.sendgrid = sendgrid or SendgridRepository()
        self.openai = openai
        self.async_openai = async_openai

    def _handle_if_existing_applicant_matches_email(
        self,
        existing_applicants_that_match_email: list[Application],
        resume_url: str | None,
        raw_text: str,
        resume_information: ExtractedResume,
        application_repository: ApplicationRepository,
        event_producer: ApplicationEventProducer,
        data: ResumeAndApplication,
    ):
        for matched_application in existing_applicants_that_match_email:
            application_repository.update_application_with_parsed_information(
                application_id=matched_application.id,
                resume_url=resume_url,
                raw_resume_text=raw_text,
                resume_information=resume_information,
            )
            event_producer.application_is_submitted(
                matched_application.company_id,
                matched_application.job_id,
                matched_application.id,
            )

        # Delete the original application
        ApplicationUseCase(self.request_scope).delete_application_for_job(
            company_id=data.company_id,
            application_id=data.application_id,
        )
        original_application_deleted = True
        return original_application_deleted

    async def _extract_and_update_application(
        self, data: ResumeAndApplication, application_repository: ApplicationRepository
    ) -> bool:
        if not self.async_openai:
            raise MissingAsyncOpenAIRepository

        if data.parse_resume:
            extractor = ResumeExtractorUseCase(self.request_scope, self.async_openai)
            if data.resume_id is None:
                raise CouldNotParseResumeText
            raw_text, resume_url = extractor.extract_resume_text_and_url(data.resume_id)
        else:
            application = application_repository.get(data.application_id)
            raw_text = application.extracted_resume_text
            resume_url = application.resume_url

        if not raw_text or len(raw_text) == 0:
            raise CouldNotParseResumeText
        resume_information = await extractor.extract_resume_information(raw_text)

        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=data.company_id, incremental_usages={UsageType.RESUME_SCANS: 1}
        )

        original_application_deleted = False

        existing_applicants_that_match_email = application_repository.query(
            email=resume_information.email,
            job_id=data.job_id,
        )[0]

        event_producer = ApplicationEventProducer(
            self.request_scope, SourceServices.API
        )
        if existing_applicants_that_match_email:
            self._handle_if_existing_applicant_matches_email(
                existing_applicants_that_match_email,
                resume_url,
                raw_text,
                resume_information,
                application_repository,
                event_producer,
                data,
            )

        application_repository.update_application_with_parsed_information(
            application_id=data.application_id,
            resume_url=resume_url,
            raw_resume_text=raw_text,
            resume_information=resume_information,
        )
        event_producer.application_is_submitted(
            data.company_id, data.job_id, data.application_id
        )
        original_application_deleted = False
        return original_application_deleted

    async def upload_resume(self) -> None:
        data = ResumeAndApplication.model_validate(self.message.data)
        application_repository = ApplicationRepository(self.request_scope)
        application = application_repository.get(data.application_id)

        # Update the scan status to started
        application_repository.update_fields(
            data.application_id, resume_scan_status=ScanStatus.STARTED
        )

        # Try to peform the parse and updates
        try:
            original_application_deleted = await self._extract_and_update_application(
                data, application_repository
            )
            if not original_application_deleted:
                application_repository.update_fields(
                    data.application_id, resume_scan_status=ScanStatus.COMPLETED
                )
        except Exception as e:
            if application.resume_scan_attempts >= 2:
                # Give up and mark as failed
                application_repository.update_fields(
                    data.application_id,
                    resume_scan_status=ScanStatus.FAILED,
                    resume_scan_error_text=str(e),
                    resume_scan_attempts=application.resume_scan_attempts + 1,
                )
            else:
                # Update count and reason and try again
                application_repository.update_fields(
                    data.application_id,
                    resume_scan_status=ScanStatus.PENDING,
                    resume_scan_error_text=str(e),
                    resume_scan_attempts=application.resume_scan_attempts + 1,
                )
                # Async wait 3 seconds then create a new event to try again
                ApplicationEventProducer(
                    self.request_scope, SourceServices.SERVICES
                ).company_uploads_resume(
                    data.company_id,
                    data.resume_id,
                    data.application_id,
                    data.job_id,
                    data.parse_resume,
                )
            raise e

    async def calculate_match_score(self) -> None:
        if not self.async_openai:
            raise MissingAsyncOpenAIRepository
        data = ApplicantAndCompany.model_validate(self.message.data)
        await ApplicantMatchUsecase(
            self.request_scope, self.async_openai
        ).update_application_with_match_score(data.application_id)
        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=data.company_id, incremental_usages={UsageType.MATCH_SCORES: 1}
        )

    async def extract_application_filters(self) -> None:
        application_repo = ApplicationRepository(self.request_scope)
        data = ApplicantAndCompany.model_validate(self.message.data)
        application = application_repo.get(data.application_id)
        job = JobRepository(self.request_scope, application.company_id).get(
            application.job_id
        )
        application.extract_filter_information(
            job_lat=job.location_override.lat if job.location_override else None,
            job_lon=job.location_override.lng if job.location_override else None,
        )
        application_repo.update(
            data.application_id,
            UpdateApplication(additional_filters=application.additional_filters),
        )

    async def answer_application_questions(self) -> None:
        if not self.async_openai:
            raise MissingAsyncOpenAIRepository
        data = ApplicantAndCompany.model_validate(self.message.data)
        question_usecase = ApplicantQuestionsUsecase(
            self.request_scope, self.async_openai
        )
        answered_questions = (
            await question_usecase.update_application_with_questions_answered(
                data.application_id
            )
        )
        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=data.company_id,
            incremental_usages={
                UsageType.APPLICATION_QUESTIONS_ANSWERED: answered_questions
            },
        )

    async def application_is_submitted(self, send_webhooks: bool = True) -> None:
        await asyncio.gather(
            self.calculate_match_score(),
            self.extract_application_filters(),
            self.answer_application_questions(),
        )

        # Send out application webhook
        if send_webhooks:
            data = ApplicantAndCompany.model_validate(self.message.data)
            CompanyApplicantsWebhookEgress(
                self.request_scope
            ).send_create_applicant_webhook(data.company_id, data.application_id)

    async def application_is_updated(self) -> None:
        data = ApplicantAndCompany.model_validate(self.message.data)
        CompanyApplicantsWebhookEgress(
            self.request_scope
        ).send_update_applicant_webhook(data.company_id, data.application_id)

    async def application_is_deleted(self) -> None:
        data = ApplicantAndCompany.model_validate(self.message.data)
        CompanyApplicantsWebhookEgress(
            self.request_scope
        ).send_delete_applicant_webhook(data.company_id, data.application_id)

    async def handle_ingress_event(self) -> None:
        data = IngressEvent.model_validate(self.message.data)
        route_transformer_request(self.request_scope, data)
