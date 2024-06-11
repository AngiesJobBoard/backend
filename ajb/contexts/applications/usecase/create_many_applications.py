from ajb.base import BaseUseCase
from ajb.base.events import SourceServices
from ajb.base.schema import Collection
from ajb.contexts.applications.constants import ApplicationConstants
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.models import CreateApplication

from .helpers import ApplicationHelpersUseCase


class CreateManyApplicationsResolver(BaseUseCase):
    def _handle_update_counts(
        self, company_id: str, job_id: str, num_created_applicants: int
    ) -> None:
        helper = ApplicationHelpersUseCase(self.request_scope)
        helper.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.TOTAL_APPLICANTS,
            num_created_applicants,
            True,
        )
        helper.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.NEW_APPLICANTS,
            num_created_applicants,
            True,
        )

    def _handle_submission_event(
        self,
        produce_submission_event: bool,
        created_applications: list[str],
        company_id: str,
        job_id: str,
    ) -> None:
        if not produce_submission_event:
            return
        event_producer = ApplicationEventProducer(
            self.request_scope, SourceServices.API
        )
        for application_id in created_applications:
            event_producer.company_gets_match_score(
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
            )

    def _handle_add_job_questions(
        self, job_id: str, partial_applications: list[CreateApplication]
    ) -> list[CreateApplication]:
        job_questions = ApplicationHelpersUseCase(self.request_scope).get_job_questions(
            job_id
        )

        # Add the job questions to each partial appliaction
        for idx in range(len(partial_applications)):
            partial_applications[idx].application_questions = job_questions
        return partial_applications

    def _handle_create_many_applications(
        self,
        partial_applications: list[CreateApplication],
    ) -> list[str]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        return application_repo.create_many(partial_applications)

    def create_many_applications(
        self,
        company_id: str,
        job_id: str,
        partial_applications: list[CreateApplication],
        produce_submission_event: bool = True,
    ) -> list[str]:
        applications_with_job_questions = self._handle_add_job_questions(
            job_id, partial_applications
        )
        created_applications = self._handle_create_many_applications(
            applications_with_job_questions
        )
        self._handle_update_counts(company_id, job_id, len(created_applications))
        self._handle_submission_event(
            produce_submission_event, created_applications, company_id, job_id
        )
        return created_applications
