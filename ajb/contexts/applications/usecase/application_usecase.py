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
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.base.models import RequestScope

from .helpers import ApplicationHelpersUseCase
from .creation import ApplicationCreationUseCase
from .updates import ApplicationUpdatesUseCase
from .ingress import ApplicationIngressUseCase
from .statistics import ApplicationStatisticsUseCase


class ApplicationUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        # Prepare repository access
        self.request_scope = request_scope
        self.storage_repo = storage or FirebaseStorageRepository()

        # Initialize each component
        self.helpers = ApplicationHelpersUseCase(self)
        self.creation = ApplicationCreationUseCase(self)
        self.updates = ApplicationUpdatesUseCase(self)
        self.ingress = ApplicationIngressUseCase(self)
        self.statistics = ApplicationStatisticsUseCase(self)

    # Passthrough creation.py methods
    def create_application(
        self,
        company_id: str,
        job_id: str,
        partial_application: CreateApplication,
        produce_submission_event: bool = True,
    ) -> Application:
        return self.creation.create_application(
            company_id, job_id, partial_application, produce_submission_event
        )

    def create_many_applications(
        self,
        company_id: str,
        job_id: str,
        partial_applications: list[CreateApplication],
        produce_submission_event: bool = True,
    ) -> list[str]:
        return self.creation.create_many_applications(
            company_id, job_id, partial_applications, produce_submission_event
        )

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        return self.creation.create_applications_from_csv(
            company_id, job_id, raw_candidates
        )

    def create_application_from_resume(
        self,
        data: UserCreateResume,
        additional_partial_data: CreateApplication | None = None,
    ) -> Application:
        return self.creation.create_application_from_resume(
            data, additional_partial_data
        )

    def application_is_created_from_raw_text(
        self, company_id: str, job_id: str, raw_text: str
    ):
        return self.creation.application_is_created_from_raw_text(
            company_id, job_id, raw_text
        )

    # Passthrough updates.py methods
    def update_application_counts(
        self,
        company_id: str,
        job_id: str,
        field: str,
        count_change: int,
        is_increase: bool,
    ):
        return self.updates.update_application_counts(
            company_id, job_id, field, count_change, is_increase
        )

    def _update_company_count_for_new_applications(
        self, original_application: Application, new_application: Application
    ):
        return self.updates._update_company_count_for_new_applications(
            original_application, new_application
        )

    def recruiter_updates_application_status(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        new_status: CreateApplicationStatusUpdate,
    ) -> CompanyApplicationView:
        return self.updates.recruiter_updates_application_status(
            company_id, job_id, application_id, new_status
        )

    # Passthrough ingress.py methods
    def process_email_application_ingress(
        self,
        ingress_email: Message,
        ingress_record: CompanyEmailIngress,
    ) -> list[Application]:
        return self.ingress.process_email_application_ingress(
            ingress_email, ingress_record
        )

    # Passthrough statistics.py methods
    def get_application_statistics(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> CompanyApplicationStatistics:
        return self.statistics.get_application_statistics(company_id, job_id)
