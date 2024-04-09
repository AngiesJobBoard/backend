from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ajb.base import BaseUseCase, Collection, RepoFilterParams, RequestScope
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.base.events import SourceServices
from ajb.common.models import ApplicationQuestion
from ajb.contexts.resumes.models import Resume, UserCreateResume, CreateResume
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.models import (
    CreateApplicationStatusUpdate,
    CompanyApplicationView,
)
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.companies.notifications.usecase import CompanyNotificationUsecase
from ajb.contexts.companies.notifications.models import (
    NotificationType,
    SystemCreateCompanyNotification,
)
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.arango.models import Filter
from ajb.utils import random_salt

from .models import CreateApplication, Application, ScanStatus
from .constants import ApplicationConstants


class ApplicationUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        self.request_scope = request_scope
        self.storage_repo = storage or FirebaseStorageRepository()

    def _create_resume_file_path(self, company_id: str, job_id: str):
        return f"{company_id}/{job_id}/resumes/{int(datetime.now().timestamp())}-{random_salt()}"

    def _get_job_questions(self, job_id):
        job: Job = self.get_object(Collection.JOBS, job_id)
        if not job.application_questions_as_strings:
            return []
        return [
            ApplicationQuestion(question=question)
            for question in job.application_questions_as_strings
        ]

    def update_application_counts(
        self,
        company_id: str,
        job_id: str,
        field: str,
        count_change: int,
        is_increase: bool,
    ):
        company_repo = self.get_repository(Collection.COMPANIES)
        job_repo = self.get_repository(
            Collection.JOBS, self.request_scope, parent_id=company_id
        )
        if is_increase:
            company_repo.increment_field(company_id, field, count_change)
            job_repo.increment_field(job_id, field, count_change)
            return
        company_repo.decrement_field(company_id, field, count_change)
        job_repo.decrement_field(job_id, field, count_change)

    def create_application(
        self,
        company_id: str,
        job_id: str,
        partial_application: CreateApplication,
        produce_submission_event: bool = True,
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        partial_application.application_questions = self._get_job_questions(job_id)
        created_application: Application = application_repo.create(partial_application)
        self.update_application_counts(
            company_id, job_id, ApplicationConstants.TOTAL_APPLICANTS, 1, True
        )
        self.update_application_counts(
            company_id, job_id, ApplicationConstants.NEW_APPLICANTS, 1, True
        )

        if produce_submission_event:
            ApplicationEventProducer(
                self.request_scope, source_service=SourceServices.API
            ).application_is_created(
                created_application.company_id,
                created_application.job_id,
                created_application.id,
            )
        return created_application

    def create_many_applications(
        self,
        company_id: str,
        job_id: str,
        partial_applications: list[CreateApplication],
        produce_submission_event: bool = True,
    ) -> list[str]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        job_questions = self._get_job_questions(job_id)
        candidates_with_job_questions = []
        for candidate in partial_applications:
            candidate.application_questions = job_questions
            candidates_with_job_questions.append(candidate)
        created_applications = application_repo.create_many(
            candidates_with_job_questions
        )
        self.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.TOTAL_APPLICANTS,
            len(created_applications),
            True,
        )
        self.update_application_counts(
            company_id,
            job_id,
            ApplicationConstants.NEW_APPLICANTS,
            len(created_applications),
            True,
        )

        if produce_submission_event:
            event_producer = ApplicationEventProducer(
                self.request_scope, SourceServices.API
            )
            for application in created_applications:
                event_producer.application_is_created(company_id, job_id, application)
        return created_applications

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        return self.create_many_applications(company_id, job_id, partial_candidates)

    def create_application_from_resume(self, data: UserCreateResume) -> Application:
        # Create an application for this resume
        resume_repo = self.get_repository(Collection.RESUMES)
        remote_file_path = self._create_resume_file_path(data.company_id, data.job_id)
        resume_url = self.storage_repo.upload_bytes(
            data.resume_data, data.file_type, remote_file_path, True
        )
        resume: Resume = resume_repo.create(
            CreateResume(
                resume_url=resume_url,
                remote_file_path=remote_file_path,
                **data.model_dump(),
            )
        )
        partial_application = CreateApplication(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            name="-",
            email="-",
            resume_scan_status=ScanStatus.PENDING,
            match_score_status=ScanStatus.PENDING,
        )
        partial_application.application_questions = self._get_job_questions(
            resume.job_id
        )
        created_application = self.create_application(
            resume.company_id, resume.job_id, partial_application, False
        )

        # Create kafka event for parsing the resume
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
        )
        return created_application

    def delete_application_for_job(
        self, company_id: str, application_id: str
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application: Application = application_repo.get(application_id)
        application_repo.delete(application_id)
        self.update_application_counts(
            company_id,
            application.job_id,
            ApplicationConstants.TOTAL_APPLICANTS,
            1,
            False,
        )
        if (
            application.application_match_score
            and application.application_match_score > 70
        ):
            self.update_application_counts(
                company_id,
                application.job_id,
                ApplicationConstants.HIGH_MATCHING_APPLICANTS,
                1,
                False,
            )
        ApplicationEventProducer(
            self.request_scope, SourceServices.API
        ).application_is_deleted(company_id, application.job_id, application_id)
        return application

    def delete_all_applications_for_job(self, company_id: str, job_id: str):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        applications: list[Application] = application_repo.query(
            repo_filters=RepoFilterParams(
                filters=[
                    Filter(field="company_id", value=company_id),
                    Filter(field="job_id", value=job_id),
                ]
            )
        )[0]

        with ThreadPoolExecutor() as executor:
            for application in applications:
                executor.submit(
                    self.delete_application_for_job, company_id, application.id
                )
        event_producer = ApplicationEventProducer(
            self.request_scope, SourceServices.API
        )
        for application in applications:
            event_producer.application_is_deleted(
                application.company_id, application.job_id, application.id
            )
        return True

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
            self.get_repository(
                Collection.APPLICATIONS, transaction_scope
            ).update_fields(
                application_id, application_status=new_status.application_status
            )
            RecruiterUpdatesRepository(transaction_scope).update_application_status(
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
            notification_message = f"{response.name} has been moved to status {new_status.application_status} for job {response.job.position_title}."
            if new_status.update_reason:
                notification_message += (
                    f"\nNote from Recruiter: {new_status.update_reason}"
                )
            CompanyNotificationUsecase(transaction_scope).create_company_notification(
                company_id=company_id,
                data=SystemCreateCompanyNotification(
                    company_id=company_id,
                    notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
                    title=f"Updated Application for job {response.job.position_title}",
                    message=notification_message,
                    application_id=application_id,
                    job_id=job_id,
                    metadata={
                        "application_status": new_status.application_status,
                        "update_reason": new_status.update_reason,
                    },
                ),
                all_but_current_recruiter=True,
            )
            return response
