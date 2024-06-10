"""
This module contains the asyncronous event handlers for the company context.
These are triggered when a company event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

from ajb.base import RequestScope
from ajb.base.events import BaseKafkaMessage, SourceServices
from ajb.contexts.applications.events import (
    ResumeAndApplication,
    ApplicantAndCompany,
    IngressEvent,
)
from ajb.contexts.applications.models import (
    ScanStatus,
    UpdateApplication,
)
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.repository import ApplicationRepository
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
    ):
        self.message = message
        self.request_scope = request_scope
        self.sendgrid = sendgrid or SendgridRepository()
        self.openai = AsyncOpenAIRepository(openai) or AsyncOpenAIRepository(
            OpenAIRepository()
        )

    async def _extract_and_update_application(
        self, data: ResumeAndApplication, application_repository: ApplicationRepository
    ) -> None:
        extractor = ResumeExtractorUseCase(self.request_scope, self.openai)
        application = application_repository.get(data.application_id)
        if application.extracted_resume_text is None:
            raise CouldNotParseResumeText
        resume_information = await extractor.extract_resume_information(
            application.extracted_resume_text
        )

        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=data.company_id, incremental_usages={UsageType.RESUME_SCANS: 1}
        )
        application_repository.update_application_with_parsed_information(
            application_id=data.application_id,
            resume_information=resume_information,
        )

    async def upload_resume(self) -> None:
        data = ResumeAndApplication.model_validate(self.message.data)
        application_repository = ApplicationRepository(self.request_scope)

        # Update the scan status to started
        application_repository.update_fields(
            data.application_id, resume_scan_status=ScanStatus.STARTED
        )

        # Try to peform the parse and updates
        try:
            await self._extract_and_update_application(data, application_repository)
            application_repository.update_fields(
                data.application_id, resume_scan_status=ScanStatus.COMPLETED
            )
            if data.send_post_application_event:
                ApplicationEventProducer(
                    self.request_scope, SourceServices.SERVICES
                ).post_application_submission(
                    company_id=data.company_id,
                    job_id=data.job_id,
                    application_id=data.application_id,
                )
        except Exception as e:
            application_repository.update_fields(
                data.application_id,
                resume_scan_status=ScanStatus.FAILED,
                resume_scan_error_text=str(e),
            )
            return

    async def company_gets_match_score(self) -> None:
        data = ApplicantAndCompany.model_validate(self.message.data)
        await ApplicantMatchUsecase(
            self.request_scope, self.openai
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
        data = ApplicantAndCompany.model_validate(self.message.data)
        question_usecase = ApplicantQuestionsUsecase(self.request_scope, self.openai)
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

    async def post_application_submission(self, send_webhooks: bool = True) -> None:
        await self.extract_application_filters()
        await self.answer_application_questions()

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
