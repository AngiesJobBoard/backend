from ajb.base import BaseUseCase
from ajb.base.events import SourceServices
from ajb.base.schema import Collection
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.models import Application, CreateApplication
from ajb.contexts.billing.validate_usage import BillingValidateUsageUseCase, UsageType

from .helpers import ApplicationHelpersUseCase


class CreateApplicationResolver(BaseUseCase):
    def _handle_update_counts(self, company_id: str, job_id: str) -> None:
        helper = ApplicationHelpersUseCase(self.request_scope)
        helper.update_application_counts(
            company_id, job_id, ApplicationConstants.TOTAL_APPLICANTS, 1, True
        )
        helper.update_application_counts(
            company_id, job_id, ApplicationConstants.NEW_APPLICANTS, 1, True
        )

    def _handle_submission_event(
        self, produce_submission_event: bool, created_application: Application
    ) -> None:
        if not produce_submission_event:
            return
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_gets_match_score(
            created_application.company_id,
            created_application.job_id,
            created_application.id,
        )

    def _handle_create_application(
        self, partial_application: CreateApplication, job_id: str
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)

        # Append default job questions to application
        partial_application.application_questions = ApplicationHelpersUseCase(
            self.request_scope
        ).get_job_questions(job_id)

        # Create appliaction
        return application_repo.create(partial_application)

    def create_application(
        self,
        company_id: str,
        job_id: str,
        partial_application: CreateApplication,
        produce_submission_event: bool = True,
    ) -> Application:
        """All roads lead to here for creating an application..."""
        BillingValidateUsageUseCase(self.request_scope, company_id).validate_usage(
            company_id, UsageType.APPLICATIONS_PROCESSED
        )
        created_application = self._handle_create_application(
            partial_application, job_id
        )
        self._handle_update_counts(company_id, job_id)
        self._handle_submission_event(produce_submission_event, created_application)
        return created_application
