from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.applications.models import Application
from ajb.exceptions import EntityNotFound

from .models import (
    UserCreatePublicApplicationForm,
    CreatePublicApplicationForm,
    PublicApplicationForm,
)


class JobNotActiveException(Exception):
    pass


class FailedToSubmitApplciationException(Exception):
    pass


class JobPublicApplicationFormUsecase(BaseUseCase):
    def get_public_job_data(self, job_id: str):
        job_repo: JobRepository = self.get_repository(Collection.JOBS)  # type: ignore
        job = job_repo.get_full_job_with_company(job_id)
        if job.active is False or job.job_is_public is False:
            raise JobNotActiveException
        return job

    def _validate_job(self, job_id: str):
        try:
            job = self.get_public_job_data(job_id)
        except (
            EntityNotFound,
            JobNotActiveException,
        ):
            raise FailedToSubmitApplciationException
        return job

    def _update_any_existing_applications_for_form(
        self, job_id: str, created_application: PublicApplicationForm
    ) -> bool:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        potential_matches: list[Application] = application_repo.get_all(
            job_id=job_id,
            email=created_application.email,
        )
        for match in potential_matches:
            # Only update if the field is null? Hmmmmm.... business logic..
            if match.application_form_id is not None:
                continue
            application_repo.update_fields(match.id, application_form_id=created_application.id)
        
        return len(potential_matches) > 0

    def submit_public_job_application(
        self, data: UserCreatePublicApplicationForm, job_id: str
    ) -> tuple[PublicApplicationForm, bool]:
        # Get/validate job
        job = self._validate_job(job_id)

        repo = self.get_repository(Collection.PUBLIC_APPLICATION_FORMS)
        created_application_form = repo.create(
            CreatePublicApplicationForm(
                company_id=job.company_id, job_id=job_id, **data.model_dump()
            )
        )
        updated_existing_applications = self._update_any_existing_applications_for_form(
            job_id, created_application_form
        )
        return created_application_form, updated_existing_applications
