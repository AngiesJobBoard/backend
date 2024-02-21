"""
This module contains the asyncronous event handlers for the company context.
These are triggered when a company event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

from ajb.base import RequestScope
from ajb.contexts.companies.models import Company
from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.contexts.companies.events import (
    RecruiterAndApplication,
    RecruiterAndApplications,
    ResumeAndApplication,
)
from ajb.contexts.applications.models import (
    Application,
    ResumeScanStatus,
    Qualifications,
    WorkHistory,
    UpdateApplication,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.companies.actions.repository import CompanyActionRepository
from ajb.contexts.companies.actions.models import CreateCompanyAction
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.applications.extract_data.usecase import ResumeExtractorUseCase
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.newly_created_company.models import (
    NewlyCreatedCompany,
)


class AsynchronousCompanyEvents:
    def __init__(
        self,
        message: BaseKafkaMessage,
        request_scope: RequestScope,
        sendgrid: SendgridRepository | None = None,
    ):
        self.message = message
        self.request_scope = request_scope
        self.sendgrid = sendgrid or SendgridRepository()

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
        application_id: str,
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
            ),
        )

    def _extract_and_update_application(
        self, data: ResumeAndApplication, application_repository: ApplicationRepository
    ):
        extractor = ResumeExtractorUseCase(self.request_scope)
        raw_text = extractor.extract_resume_text(data.resume_id)
        resume_information = extractor.extract_resume_information(raw_text)

        existing_applicants_that_match_email: list[Application] = (
            application_repository.query(
                email=resume_information.email,
                job_id=data.job_id,
            )[0]
        )

        if existing_applicants_that_match_email:
            for matched_application in existing_applicants_that_match_email:
                self._update_application_with_parsed_information(
                    matched_application.id,
                    raw_text,
                    resume_information,
                    application_repository,
                )
            return
        self._update_application_with_parsed_information(
            data.application_id, raw_text, resume_information, application_repository
        )

    async def company_uploads_resume(self):
        data = ResumeAndApplication.model_validate(self.message.data)
        application_repository = ApplicationRepository(self.request_scope)

        # Update the scan status to started
        application_repository.update_fields(
            data.application_id, resume_scan_status=ResumeScanStatus.STARTED
        )

        # Try to peform the parse and updates
        try:
            self._extract_and_update_application(data, application_repository)
            application_repository.update_fields(
                data.application_id, resume_scan_status=ResumeScanStatus.COMPLETED
            )

            # Trigger event to perform matching again
        except Exception as e:
            application_repository.update_fields(
                data.application_id,
                resume_scan_status=ResumeScanStatus.FAILED,
                resume_scan_error_text=str(e),
            )
            raise e
