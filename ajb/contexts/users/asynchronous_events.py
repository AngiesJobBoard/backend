"""
This module contains the asyncronous event handlers for the user context.
These are triggered when a user event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

from ajb.base import RequestScope
from ajb.base.events import UserEvent, BaseKafkaMessage
from ajb.contexts.users.models import User
from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.vendor.algolia.models import InsightsEvent, InsightsAction
from ajb.contexts.users.events import (
    UserAndJob,
    UserAndJobs,
    UserAndCompany,
    UserAndCompanies,
    UserJobAndApplication,
)
from ajb.contexts.users.actions.repository import UserActionRepository
from ajb.contexts.users.actions.models import CreateUserAction
from ajb.contexts.companies.notifications.repository import (
    CompanyNotificationRepository,
    CreateCompanyNotification,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.users.repository import UserRepository, User
from ajb.contexts.users.resumes.repository import ResumeRepository
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.vendor.sendgrid.templates.new_application.models import JobApplicationData
from ajb.vendor.sendgrid.templates.new_user.models import NewUserWelcomeData
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaIndex,
)
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.clerk.repository import ClerkAPIRepository


class AsynchronousUserEvents:
    def __init__(
        self,
        message: BaseKafkaMessage,
        request_scope: RequestScope,
        search_candidates: AlgoliaSearchRepository | None = None,
        job_insights: AlgoliaInsightsRepository | None = None,
        company_insights: AlgoliaInsightsRepository | None = None,
        openai: OpenAIRepository | None = None,
        sendgrid: SendgridRepository | None = None,
        clerk: ClerkAPIRepository | None = None,
    ):
        self.message = message
        self.request_scope = request_scope
        self.search_candidates = search_candidates or AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES
        )
        self.job_insights = job_insights or AlgoliaInsightsRepository(AlgoliaIndex.JOBS)
        self.company_insights = company_insights or AlgoliaInsightsRepository(
            AlgoliaIndex.COMPANIES
        )
        self.openai = openai or OpenAIRepository()
        self.sendgrid = sendgrid or SendgridRepository()
        self.clerk = clerk or ClerkAPIRepository()

    async def user_applies_to_job(self) -> None:
        data = UserJobAndApplication.model_validate(self.message.data)

        # Update application with matching results
        application = ApplicationRepository(self.request_scope).get(data.application_id)
        ApplicantMatchUsecase(
            self.request_scope, self.openai
        ).update_application_with_match_score(application)

        # Create user action
        UserActionRepository(self.request_scope).create(
            CreateUserAction(
                action=UserEvent.USER_APPLIES_JOB,
                job_id=data.job_id,
                company_id=data.company_id,
                user_is_anonymous=data.user_is_anonymous,
            )
        )

        # Send Algolia event
        self.job_insights.send_event(
            InsightsEvent(
                eventType=InsightsAction.CONVERSION,
                eventName=UserEvent.USER_APPLIES_JOB.value,
                userToken=self.request_scope.user_id,
                objectIDs=[data.job_id],
            )
        )

        # Notification and email to company's recruiters about new application
        company = CompanyRepository(self.request_scope).get(data.company_id)
        job = JobRepository(self.request_scope, data.company_id).get(data.job_id)
        user = UserRepository(self.request_scope).get(data.user_id)
        first_name, last_initial = user.first_name, user.last_name[0].capitalize()
        resume = ResumeRepository(self.request_scope, data.user_id).get(data.resume_id)
        CompanyNotificationRepository(self.request_scope, data.company_id).create(
            CreateCompanyNotification(
                company_id=data.company_id,
                notification_type=UserEvent.USER_APPLIES_JOB,
                title=f"New application for {job.position_title}!",
                message=f"{first_name} {last_initial} has applied for your position: {job.position_title}!",
                candidate_id=self.request_scope.user_id,
                job_id=data.job_id,
            )
        )

        email_template = self.sendgrid.format_email_template(
            "new_application",
            template_data=JobApplicationData(
                position=str(job.position_title),
                company=company.name,
                name=f"{first_name} {user.last_name}",
                email=user.email,
                phone=user.phone_number,
                resumeLink=resume.resume_url,
            ),
        )

        # Send company email about new applicant
        company_recruiters, _ = RecruiterRepository(
            self.request_scope, data.company_id
        ).get_recruiters_by_company(data.company_id)
        for recruiter in company_recruiters:
            if not recruiter.send_new_application_updates:
                continue
            self.sendgrid.send_email(
                to_emails=email_template,
                subject=f"New Application for {job.position_title}!",
                html_content=email_template,
            )

    async def user_is_created(self) -> None:
        user = UserRepository(self.request_scope).get(self.message.data["user_id"])
        email_template = self.sendgrid.format_email_template(
            "new_user",
            template_data=NewUserWelcomeData(
                firstName=user.first_name,
            ),
        )
        self.sendgrid.send_email(
            to_emails=user.email,
            subject="Welcome to Angie's Job Board!",
            html_content=email_template,
        )

    async def user_is_deleted(self) -> None:
        user_id = self.message.data["user_id"]
        self.search_candidates.delete_object(user_id)
        self.clerk.delete_user(user_id)

    async def user_is_updated(self) -> None:
        user = User.model_validate(self.message.data)
        if user.profile_is_public:
            self.search_candidates.update_object(user.id, user.model_dump())

    async def user_views_jobs(self) -> None:
        data = UserAndJobs.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create_many(
            [
                CreateUserAction(
                    action=UserEvent.USER_VIEWS_JOBS,
                    job_id=job_id,
                    company_id=company_id,
                    position=position,
                    user_is_anonymous=data.user_is_anonymous,
                )
                for company_id, job_id, position in data.companies_jobs_and_positions
            ]
        )

    async def user_clicks_job(self) -> None:
        data = UserAndJob.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create(
            CreateUserAction(
                action=UserEvent.USER_CLICKS_JOB,
                job_id=data.job_id,
                company_id=data.company_id,
                user_is_anonymous=data.user_is_anonymous,
            )
        )
        self.job_insights.send_event(
            InsightsEvent(
                eventType=InsightsAction.CLICK,
                eventName=UserEvent.USER_CLICKS_JOB.value,
                userToken=self.request_scope.user_id,
                objectIDs=[data.job_id],
            )
        )

    async def user_saves_job(self) -> None:
        data = UserAndJob.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create(
            CreateUserAction(
                action=UserEvent.USER_SAVES_JOB,
                job_id=data.job_id,
                company_id=data.company_id,
                user_is_anonymous=data.user_is_anonymous,
            )
        )
        self.job_insights.send_event(
            InsightsEvent(
                eventType=InsightsAction.CONVERSION,
                eventName=UserEvent.USER_SAVES_JOB.value,
                userToken=self.request_scope.user_id,
                objectIDs=[data.job_id],
            )
        )

    async def user_views_companies(self) -> None:
        data = UserAndCompanies.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create_many(
            [
                CreateUserAction(
                    action=UserEvent.USER_VIEWS_COMPANIES,
                    company_id=company_id,
                    position=position,
                    user_is_anonymous=data.user_is_anonymous,
                )
                for company_id, position in data.companies_and_positions
            ]
        )

    async def user_clicks_company(self) -> None:
        data = UserAndCompany.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create(
            CreateUserAction(
                action=UserEvent.USER_CLICKS_COMPANY,
                company_id=data.company_id,
                user_is_anonymous=data.user_is_anonymous,
            )
        )
        self.company_insights.send_event(
            InsightsEvent(
                eventType=InsightsAction.CLICK,
                eventName=UserEvent.USER_CLICKS_COMPANY.value,
                userToken=self.request_scope.user_id,
                objectIDs=[data.company_id],
            )
        )

    async def user_saves_company(self) -> None:
        data = UserAndCompany.model_validate(self.message.data)
        UserActionRepository(self.request_scope).create(
            CreateUserAction(
                action=UserEvent.USER_SAVES_COMPANY,
                company_id=data.company_id,
                user_is_anonymous=data.user_is_anonymous,
            )
        )
        self.company_insights.send_event(
            InsightsEvent(
                eventType=InsightsAction.CONVERSION,
                eventName=UserEvent.USER_SAVES_COMPANY.value,
                userToken=self.request_scope.user_id,
                objectIDs=[data.company_id],
            )
        )
