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
    CompanyAndJob,
)
from ajb.contexts.companies.actions.repository import (
    CompanyActionRepository,
    CreateCompanyAction,
)
from ajb.contexts.companies.email_ingress_webhooks.repository import (
    CompanyEmailIngressRepository,
)
from ajb.contexts.companies.email_ingress_webhooks.models import (
    CreateCompanyEmailIngress,
    EmailIngressType,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.companies.api_ingress_webhooks.models import CreateCompanyAPIIngress
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.webhooks.egress.jobs.usecase import CompanyJobWebhookEgress
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.newly_created_company import NewlyCreatedCompany
from ajb.vendor.openai.repository import OpenAIRepository, AsyncOpenAIRepository


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

    def create_company_subdomain_and_webhook_secrets(self, company_id: str):
        """
        For emails we need a subdomain generated
        For API webhooks we a full JWT provided
        """

        # Create the email ingress subdomain relationships
        CompanyEmailIngressRepository(self.request_scope, company_id).create(
            CreateCompanyEmailIngress.generate(company_id, EmailIngressType.CREATE_JOB)
        )

        # Create the API ingress JWT relationship
        CompanyAPIIngressRepository(self.request_scope, company_id).set_sub_entity(
            CreateCompanyAPIIngress.generate(company_id)
        )

    async def company_is_created(self) -> None:
        created_company = Company.model_validate(self.message.data)
        user = UserRepository(self.request_scope).get(self.request_scope.user_id)
        self.create_company_subdomain_and_webhook_secrets(created_company.id)
        self.sendgrid.send_email_template(
            to_emails=user.email,
            subject="Welcome to Angie's Job Board!",
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

    async def company_creates_job(self) -> None:
        data = CompanyAndJob.model_validate(self.message.data)

        # Create email ingress record
        CompanyEmailIngressRepository(self.request_scope).create(
            CreateCompanyEmailIngress.generate(
                data.company_id, EmailIngressType.CREATE_APPLICATION, data.job_id
            )
        )

        # Send out job creation webhooks
        CompanyJobWebhookEgress(self.request_scope).send_create_job_webhook(
            data.company_id, data.job_id
        )

    async def company_updates_job(self) -> None:
        data = CompanyAndJob.model_validate(self.message.data)
        CompanyJobWebhookEgress(self.request_scope).send_update_job_webhook(
            data.company_id, data.job_id
        )
    
    async def company_deletes_job(self) -> None:
        data = CompanyAndJob.model_validate(self.message.data)
        CompanyJobWebhookEgress(self.request_scope).send_delete_job_webhook(
            data.company_id, data.job_id
        )
