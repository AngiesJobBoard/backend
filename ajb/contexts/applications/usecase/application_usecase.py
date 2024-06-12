from email.message import Message
from ajb.base.usecase import BaseUseCase
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.applications.models import (
    CompanyApplicationView,
    CreateApplication,
    Application,
    CreateApplicationStatusUpdate,
    CompanyApplicationStatistics,
)

from .create_application import CreateApplicationResolver
from .create_many_applications import CreateManyApplicationsResolver
from .create_application_from_csv import CreateManyApplicationsFromCSVResolver
from .create_application_from_resume import CreateApplicationFromResumeResolver
from .create_application_from_raw_text import CreateApplicationFromRawTextResolver
from .create_application_from_email_ingress import ApplicationEmailIngressResolver
from .handle_recruiter_status_update import RecruiterUpdateStatusResolver
from .handle_get_statistics import ApplicationStatisticsResolver
from .helpers import ApplicationHelpersUseCase


class ApplicationUseCase(BaseUseCase):
    def create_application(
        self,
        company_id: str,
        job_id: str,
        partial_application: CreateApplication,
        produce_submission_event: bool = True,
    ) -> Application:
        return CreateApplicationResolver(self.request_scope).create_application(
            company_id, job_id, partial_application, produce_submission_event
        )

    def create_many_applications(
        self,
        company_id: str,
        job_id: str,
        partial_applications: list[CreateApplication],
        produce_submission_event: bool = True,
    ) -> list[str]:
        return CreateManyApplicationsResolver(
            self.request_scope
        ).create_many_applications(
            company_id, job_id, partial_applications, produce_submission_event
        )

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        return CreateManyApplicationsFromCSVResolver(
            self.request_scope
        ).create_applications_from_csv(company_id, job_id, raw_candidates)

    def create_application_from_resume(
        self,
        data: UserCreateResume,
        additional_partial_data: CreateApplication | None = None,
    ) -> Application:
        return CreateApplicationFromResumeResolver(
            self.request_scope
        ).create_application_from_resume(data, additional_partial_data)

    def application_is_created_from_raw_text(
        self, company_id: str, job_id: str, raw_text: str
    ):
        return CreateApplicationFromRawTextResolver(
            self.request_scope
        ).application_is_created_from_raw_text(company_id, job_id, raw_text)

    def process_email_application_ingress(
        self,
        ingress_email: Message,
        ingress_record: CompanyEmailIngress,
    ) -> list[Application]:
        return ApplicationEmailIngressResolver(
            self.request_scope
        ).process_email_application_ingress(ingress_email, ingress_record)

    def get_application_statistics(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> CompanyApplicationStatistics:
        return ApplicationStatisticsResolver(
            self.request_scope
        ).get_application_statistics(company_id, job_id)

    def update_application_counts(
        self,
        company_id: str,
        job_id: str,
        field: str,
        count_change: int,
        is_increase: bool,
    ):
        return ApplicationHelpersUseCase(self.request_scope).update_application_counts(
            company_id, job_id, field, count_change, is_increase
        )

    def recruiter_updates_application_status(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        new_status: CreateApplicationStatusUpdate,
    ) -> CompanyApplicationView:
        return RecruiterUpdateStatusResolver(
            self.request_scope
        ).recruiter_updates_application_status(
            company_id, job_id, application_id, new_status
        )
