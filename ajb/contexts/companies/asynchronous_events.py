"""
This module contains the asyncronous event handlers for the company context.
These are triggered when a company event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

from ajb.base import RequestScope
from ajb.contexts.companies.models import Company
from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.vendor.algolia.models import InsightsEvent, InsightsAction
from ajb.contexts.companies.events import (
    RecruiterAndApplication,
    RecruiterAndApplications,
    RecruiterAndCandidate,
    RecruiterAndCandidates,
)
from ajb.contexts.companies.actions.repository import CompanyActionRepository
from ajb.contexts.companies.actions.models import CreateCompanyAction
from ajb.contexts.users.notifications.repository import (
    UserNotificationRepository,
    CreateUserNotification,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.repository import CompanyRepository
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaIndex,
)
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.newly_created_company.models import (
    NewlyCreatedCompany,
)
from ajb.vendor.sendgrid.templates.company_shortlists_user.models import (
    CompanyShortlistsUser,
)
from ajb.vendor.sendgrid.templates.company_rejects_user.models import (
    CompanyRejectsUser,
)
from ajb.vendor.sendgrid.templates.company_saves_user.models import CompanySavesUser


class AsynchronousCompanyEvents:
    def __init__(
        self,
        message: BaseKafkaMessage,
        request_scope: RequestScope,
        search_companies: AlgoliaSearchRepository | None = None,
        candidate_insights: AlgoliaInsightsRepository | None = None,
        sendgrid: SendgridRepository | None = None,
    ):
        self.message = message
        self.request_scope = request_scope
        self.search_companies = search_companies or AlgoliaSearchRepository(
            AlgoliaIndex.COMPANIES
        )
        self.candidate_insights = candidate_insights or AlgoliaInsightsRepository(
            AlgoliaIndex.CANDIDATES
        )
        self.sendgrid = sendgrid or SendgridRepository()

    async def company_is_created(self):
        created_company = Company.model_validate(self.message.data)
        self.search_companies.create_object(
            created_company.id, created_company.model_dump()
        )
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

    async def company_is_deleted(self):
        self.search_companies.delete_object(self.message.data["company_id"])

    async def company_is_updated(self):
        updated_company = Company.model_validate(self.message.data)
        self.search_companies.update_object(
            updated_company.id, updated_company.model_dump()
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
        application = ApplicationRepository(self.request_scope).get(data.application_id)
        job = JobRepository(self.request_scope, application.company_id).get(
            application.job_id
        )
        company = CompanyRepository(self.request_scope).get(application.company_id)
        UserNotificationRepository(self.request_scope).create(
            CreateUserNotification(
                user_id=application.user_id,
                notification_type=CompanyEvent.COMPANY_CLICKS_ON_APPLICATION,
                title="Your application has been viewed!",
                message=f"Your application for {job.position_title} has been viewed!",
                company_id=application.company_id,
                job_id=application.job_id,
                metadata={
                    "job_title": job.position_title,
                    "company_name": company.name,
                    "viewing_recruiter": self.request_scope.user_id,
                },
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

        # User notification for application being shortlisted
        application = ApplicationRepository(self.request_scope).get(data.application_id)
        job = JobRepository(self.request_scope, application.company_id).get(
            application.job_id
        )
        company = CompanyRepository(self.request_scope).get(application.company_id)
        UserNotificationRepository(self.request_scope).create(
            CreateUserNotification(
                user_id=application.user_id,
                notification_type=CompanyEvent.COMPANY_SHORTLISTS_APPLICATION,
                title="Your application has been shortlisted!",
                message=f"Your application for {job.position_title} has been shortlisted!",
                company_id=application.company_id,
                job_id=application.job_id,
                metadata={
                    "job_title": job.position_title,
                    "company_name": company.name,
                    "viewing_recruiter": self.request_scope.user_id,
                },
            )
        )

        # Send user email for application being shortlisted
        user = UserRepository(self.request_scope).get(application.user_id)
        self.sendgrid.send_rendered_email_template(
            to_emails=user.email,
            subject=f"{company.name} has shortlisted your application!",
            template_name="company_shortlists_user",
            template_data=CompanyShortlistsUser(
                position=str(job.position_title),
                candidate_name=user.first_name,
                company_name=company.name,
                application_date=application.created_at.strftime("%B %d, %Y"),
            ),
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

        # User notification for application being rejected
        application = ApplicationRepository(self.request_scope).get(data.application_id)
        job = JobRepository(self.request_scope, application.company_id).get(
            application.job_id
        )
        company = CompanyRepository(self.request_scope).get(application.company_id)
        UserNotificationRepository(self.request_scope).create(
            CreateUserNotification(
                user_id=application.user_id,
                notification_type=CompanyEvent.COMPANY_REJECTS_APPLICATION,
                title="Your application has been rejected.",
                message=f"Your application for {job.position_title} has been rejected.",
                company_id=application.company_id,
                job_id=application.job_id,
                metadata={
                    "job_title": job.position_title,
                    "company_name": company.name,
                    "viewing_recruiter": self.request_scope.user_id,
                    "application_history": application.application_status_history,
                },
            )
        )
        user = UserRepository(self.request_scope).get(application.user_id)
        self.sendgrid.send_rendered_email_template(
            to_emails=user.email,
            subject=f"{company.name} has rejected your application.",
            template_name="company_rejects_user",
            template_data=CompanyRejectsUser(
                candidate_name=user.first_name,
                position=str(job.position_title),
                company_name=company.name,
            ),
        )

    async def company_views_candidates(self):
        data = RecruiterAndCandidates.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create_many(
            [
                CreateCompanyAction(
                    action=CompanyEvent.COMPANY_VIEWS_CANDIDATES,
                    candidate_user_id=candidate_user_id,
                    position=position,
                    company_id=data.company_id,
                )
                for candidate_user_id, position in data.candidates_and_positions
            ]
        )

    async def company_clicks_candidate(self):
        data = RecruiterAndCandidate.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_CLICKS_CANDIDATE,
                candidate_user_id=data.candidate_id,
                company_id=data.company_id,
            )
        )
        self.candidate_insights.send_event(
            InsightsEvent(
                userToken=self.request_scope.user_id,
                objectIDs=[data.candidate_id],
                eventType=InsightsAction.CLICK,
                eventName=CompanyEvent.COMPANY_CLICKS_CANDIDATE.value,
            )
        )

    async def company_saves_candidate(self):
        data = RecruiterAndCandidate.model_validate(self.message.data)
        CompanyActionRepository(self.request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_SAVES_CANDIDATE,
                candidate_user_id=data.candidate_id,
                company_id=data.company_id,
            )
        )
        self.candidate_insights.send_event(
            InsightsEvent(
                userToken=self.request_scope.user_id,
                objectIDs=[data.candidate_id],
                eventType=InsightsAction.CONVERSION,
                eventName=CompanyEvent.COMPANY_SAVES_CANDIDATE.value,
            )
        )

        # User notification for candidate being saved
        company = CompanyRepository(self.request_scope).get(data.company_id)
        UserNotificationRepository(self.request_scope).create(
            CreateUserNotification(
                user_id=data.candidate_id,
                notification_type=CompanyEvent.COMPANY_SAVES_CANDIDATE,
                title="A company has saved your profile!",
                message=f"{company.name} has saved your profile!",
                metadata={
                    "viewing_recruiter": self.request_scope.user_id,
                },
            )
        )
        user = UserRepository(self.request_scope).get(data.candidate_id)
        self.sendgrid.send_rendered_email_template(
            to_emails=user.email,
            subject=f"{company.name} has saved your profile!",
            template_name="company_saves_user",
            template_data=CompanySavesUser(
                candidate_name=data.candidate_id,
            ),
        )
