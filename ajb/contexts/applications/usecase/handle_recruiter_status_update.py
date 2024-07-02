from ajb.base import BaseUseCase
from ajb.base.schema import Collection
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.applications.models import (
    Application,
    CompanyApplicationView,
    CreateApplicationStatusUpdate,
)
from ajb.contexts.applications.recruiter_updates.usecase import RecruiterUpdatesUseCase
from ajb.contexts.applications.repository import CompanyApplicationRepository

from .helpers import ApplicationHelpersUseCase


class RecruiterUpdateStatusResolver(BaseUseCase):

    def _update_company_count_for_new_applications(
        self, original_application: Application, new_application: Application
    ):
        if (
            original_application.application_status is not None
            or new_application.application_status is None
        ):
            return
        ApplicationHelpersUseCase(self.request_scope).update_application_counts(
            company_id=new_application.company_id,
            job_id=new_application.job_id,
            field=ApplicationConstants.NEW_APPLICANTS,
            count_change=1,
            is_increase=False,
        )

    def recruiter_updates_application_status(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        new_status: CreateApplicationStatusUpdate,
    ) -> CompanyApplicationView:
        with self.request_scope.start_transaction(
            read_collections=[Collection.APPLICATIONS, Collection.JOBS],
            write_collections=[
                Collection.APPLICATIONS,
                Collection.APPLICATION_RECRUITER_UPDATES,
                Collection.COMPANY_NOTIFICATIONS,
            ],
        ) as transaction_scope:
            application_repo = self.get_repository(
                Collection.APPLICATIONS, transaction_scope
            )
            original_application: Application = application_repo.get(application_id)

            assert original_application.job_id == job_id
            assert original_application.company_id == company_id

            application_repo.update_fields(
                application_id, application_status=new_status.application_status
            )
            RecruiterUpdatesUseCase(transaction_scope).update_application_status(
                company_id,
                job_id,
                application_id,
                self.request_scope.user_id,
                new_status.application_status,
                new_status.update_reason,
            )
            response = CompanyApplicationRepository(
                transaction_scope
            ).get_company_view_single(application_id)
            self._update_company_count_for_new_applications(
                original_application, response
            )
            return response
