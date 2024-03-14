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
)
from ajb.contexts.applications.models import (
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
from ajb.contexts.applications.application_questions.usecase import ApplicantQuestionsUsecase
from ajb.contexts.companies.jobs.repository import JobRepository
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

    async def company_is_created(self) -> None:
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

    async def company_views_applications(self) -> None:
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

    async def company_clicks_on_application(self) -> None:
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_CLICKS_ON_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )

    async def company_shortlists_application(self) -> None:
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_SHORTLISTS_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )

    async def company_rejects_application(self) -> None:
        data = RecruiterAndApplication.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_REJECTS_APPLICATION,
                application_id=data.application_id,
                company_id=data.company_id,
            )
        )
