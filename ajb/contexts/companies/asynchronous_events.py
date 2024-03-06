"""
This module contains the asyncronous event handlers for the company context.
These are triggered when a company event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""
import asyncio

from ajb.base import RequestScope
from ajb.contexts.companies.models import Company
from ajb.base.events import CompanyEvent, BaseKafkaMessage, SourceServices
from ajb.common.models import Location
from ajb.contexts.companies.events import (
    RecruiterAndApplication,
    RecruiterAndApplications,
    ResumeAndApplication,
    ApplicationId,
)
from ajb.contexts.applications.models import (
    Application,
    ScanStatus,
    Qualifications,
    WorkHistory,
    UpdateApplication,
)
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.companies.actions.repository import CompanyActionRepository
from ajb.contexts.companies.actions.models import CreateCompanyAction
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.applications.extract_data.usecase import ResumeExtractorUseCase
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.newly_created_company.models import (
    NewlyCreatedCompany,
)
from ajb.vendor.openai.repository import OpenAIRepository, AsyncOpenAIRepository
from ajb.contexts.companies.events import CompanyEventProducer


class AsynchronousCompanyEvents:
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

    async def company_is_created(self):
        created_company = Company.model_validate(self.message.data)
        user = UserRepository(self.request_scope).get(self.request_scope.user_id)
        self.sendgrid.send_rendered_email_template(
            to_emails=user.email,
            subject="Welcome to Angie's Job Board!",
            template_name="newly_created_company",
            template_data=NewlyCreatedCompany(
                companyName=created_company.name,
                supportEmail="support@angiesjobboard.com",
            ),
        )

    async def company_views_applications(self):
        data = RecruiterAndApplications.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create_many(
            [
                CreateCompanyAction(
                    action=CompanyEvent.COMPANY_VIEWS_APPLICATIONS,
                    application_id=application_id,
                    position=position,
                    company_id=data.company_id,
                )
                for application_id, position in data.applications_and_positions
            ]
        )

    async def company_clicks_on_application(self):
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_CLICKS_ON_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )

    async def company_shortlists_application(self):
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_SHORTLISTS_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )

    async def company_rejects_application(self):
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_REJECTS_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )

    def _update_application_with_parsed_information(
        self,
        *,
        application_id: str,
        resume_url: str,
        raw_resume_text: str,
        resume_information: ExtractedResume,
        application_repository: ApplicationRepository,
    ):
        application_repository.update(
            application_id,
            UpdateApplication(
                name=f"{resume_information.first_name} {resume_information.last_name}".title(),
                email=resume_information.email,
                phone=resume_information.phone_number,
                extracted_resume_text=raw_resume_text,
                resume_url=resume_url,
                qualifications=Qualifications(
                    most_recent_job=(
                        WorkHistory(
                            job_title=resume_information.most_recent_job_title,
                            company_name=resume_information.most_recent_job_company,
                        )
                        if resume_information.most_recent_job_title
                        and resume_information.most_recent_job_company
                        else None
                    ),
                    work_history=resume_information.work_experience,
                    education=resume_information.education,
                    skills=resume_information.skills,
                    licenses=resume_information.licenses,
                    certifications=resume_information.certifications,
                    language_proficiencies=resume_information.languages,
                ),
                user_location=(
                    Location(
                        city=resume_information.city, state=resume_information.state
                    )
                    if resume_information.city and resume_information.state
                    else None
                ),
            ),
        )

    async def _extract_and_update_application(
        self, data: ResumeAndApplication, application_repository: ApplicationRepository
    ) -> bool:
        if not self.async_openai:
            raise RuntimeError("Async OpenAI Repository is not provided")

        extractor = ResumeExtractorUseCase(self.request_scope, self.async_openai)
        raw_text, resume_url = extractor.extract_resume_text_and_url(data.resume_id)
        resume_information = await extractor.extract_resume_information(raw_text)
        original_application_deleted = False

        existing_applicants_that_match_email: list[Application] = (
            application_repository.query(
                email=resume_information.email,
                job_id=data.job_id,
            )[0]
        )

        self.request_scope.company_id = data.company_id
        event_producter = CompanyEventProducer(self.request_scope, SourceServices.API)
        if existing_applicants_that_match_email:
            for matched_application in existing_applicants_that_match_email:
                self._update_application_with_parsed_information(
                    application_id=matched_application.id,
                    resume_url=resume_url,
                    raw_resume_text=raw_text,
                    resume_information=resume_information,
                    application_repository=application_repository,
                )
                event_producter.company_calculates_match_score(matched_application.id)

            # Delete the original application (like a merge operation)
            application_repository.delete(data.application_id)
            original_application_deleted = True
            return original_application_deleted
        self._update_application_with_parsed_information(
            application_id=data.application_id,
            resume_url=resume_url,
            raw_resume_text=raw_text,
            resume_information=resume_information,
            application_repository=application_repository,
        )
        event_producter.company_calculates_match_score(data.application_id)
        original_application_deleted = False
        return original_application_deleted

    async def company_uploads_resume(self):
        data = ResumeAndApplication.model_validate(self.message.data)
        application_repository = ApplicationRepository(self.request_scope)

        # Get the resume to see if it has been attempted 3 times
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
                    resume_scan_error_text=str(e),
                    resume_scan_attempts=application.resume_scan_attempts + 1,
                )
                # Async wait 3 seconds then create a new event to try again
                await asyncio.sleep(3)
                self.request_scope.company_id = data.company_id
                CompanyEventProducer(self.request_scope, SourceServices.SERVICES).company_uploads_resume(
                    data.resume_id, data.application_id, data.job_id
                )
            raise e

    async def company_calculates_match_score(self):
        if not self.async_openai:
            raise RuntimeError("Async OpenAI Repository is not provided")
        data = ApplicationId.model_validate(self.message.data)
        matcher_usecase = ApplicantMatchUsecase(self.request_scope, self.async_openai)
        await matcher_usecase.update_application_with_match_score(data.application_id)
