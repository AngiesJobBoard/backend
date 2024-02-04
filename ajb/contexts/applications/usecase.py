from ajb.base import Collection, BaseUseCase
from ajb.base.events import SourceServices
from ajb.contexts.companies.jobs.models import Job
from ajb.exceptions import EntityNotFound, FailedToCreateApplication
from ajb.contexts.users.events import UserEventProducer

from .models import UserCreatedApplication, CreateApplication, Application
from .enumerations import ApplicationStatus


class ApplicationsUseCase(BaseUseCase):
    def user_creates_application(
        self,
        user_id: str,
        create_application: UserCreatedApplication,
    ) -> Application:
        job_repo = self.get_repository(
            Collection.JOBS, parent_id=create_application.company_id
        )
        resume_repo = self.get_repository(Collection.RESUMES, parent_id=user_id)
        application_repo = self.get_repository(Collection.APPLICATIONS)

        # Check that the company and job is still viable
        job: Job = job_repo.get(create_application.job_id)
        if job.position_filled:
            raise FailedToCreateApplication("Job has been filled")

        # Check that user hasn't already applied to this job
        try:
            application_repo.get_one(
                user_id=user_id,
                job_id=create_application.job_id,
            )
            raise FailedToCreateApplication("You have already applied to this job")
        except EntityNotFound:
            pass

        # Check that resume exists
        assert resume_repo.get(create_application.resume_id)

        # Create the application
        application: Application = application_repo.create(
            data=CreateApplication(
                user_id=user_id,
                job_id=create_application.job_id,
                resume_id=create_application.resume_id,
                company_id=create_application.company_id,
                application_status=ApplicationStatus.SUBMITTED_FOR_ADMIN_REVIEW,
            )
        )

        # Produce Application Event
        UserEventProducer(self.request_scope, SourceServices.API).user_applies_job(
            company_id=create_application.company_id,
            job_id=create_application.job_id,
            application_id=application.id,
            resume_id=create_application.resume_id,
        )
        return application
