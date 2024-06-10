from ajb.base.schema import Collection
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.applications.models import (
    Application,
    CompanyApplicationView,
    CreateApplicationStatusUpdate,
)
from ajb.contexts.applications.recruiter_updates.usecase import RecruiterUpdatesUseCase
from ajb.contexts.applications.repository import CompanyApplicationRepository


class ApplicationUpdatesUseCase:
    def __init__(self, main):
        self.main = main

    def update_application_counts(
        self,
        company_id: str,
        job_id: str,
        field: str,
        count_change: int,
        is_increase: bool,
    ):
        company_repo = self.main.get_repository(Collection.COMPANIES)
        job_repo = self.main.get_repository(
            Collection.JOBS, self.main.request_scope, parent_id=company_id
        )
        if is_increase:
            company_repo.increment_field(company_id, field, count_change)
            job_repo.increment_field(job_id, field, count_change)
            return
        company_repo.decrement_field(company_id, field, count_change)
        job_repo.decrement_field(job_id, field, count_change)

    def _update_company_count_for_new_applications(
        self, original_application: Application, new_application: Application
    ):
        if (
            original_application.application_status is not None
            or new_application.application_status is None
        ):
            return
        self.update_application_counts(
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
        with self.main.request_scope.start_transaction(
            read_collections=[Collection.APPLICATIONS, Collection.JOBS],
            write_collections=[
                Collection.APPLICATIONS,
                Collection.APPLICATION_RECRUITER_UPDATES,
                Collection.COMPANY_NOTIFICATIONS,
            ],
        ) as transaction_scope:
            application_repo = self.main.get_repository(
                Collection.APPLICATIONS, transaction_scope
            )
            original_application: Application = application_repo.get(application_id)
            application_repo.update_fields(
                application_id, application_status=new_status.application_status
            )
            RecruiterUpdatesUseCase(transaction_scope).update_application_status(
                company_id,
                job_id,
                application_id,
                self.main.request_scope.user_id,
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
