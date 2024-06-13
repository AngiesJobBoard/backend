from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.exceptions import EntityNotFound

from .models import UserCreatePublicApplicationForm, CreatePublicApplicationForm, PublicApplicationForm


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

    def submit_public_job_application(
        self, data: UserCreatePublicApplicationForm, job_id: str
    ) -> PublicApplicationForm:
        # First check the job is valid
        try:
            job = self.get_public_job_data(job_id)
        except (
            EntityNotFound,
            JobNotActiveException,
        ):
            raise FailedToSubmitApplciationException

        repo = self.get_repository(Collection.PUBLIC_APPLICATION_FORMS)
        return repo.create(
            CreatePublicApplicationForm(
                company_id=job.company_id, job_id=job_id, **data.model_dump()
            )
        )
