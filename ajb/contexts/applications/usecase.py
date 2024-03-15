from concurrent.futures import ThreadPoolExecutor

from ajb.base import BaseUseCase, Collection, RepoFilterParams
from ajb.base.events import SourceServices
from ajb.common.models import ApplicationQuestion
from ajb.contexts.resumes.models import Resume
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.vendor.arango.models import Filter

from .models import CreateApplication, Application, ScanStatus
from .constants import ApplicationConstants


class ApplicationUseCase(BaseUseCase):

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
        created_application = application_repo.create(partial_application)
        self.update_application_counts(
            company_id, job_id, ApplicationConstants.TOTAL_APPLICANTS, 1, True
        )
        self.update_application_counts(
            company_id, job_id, ApplicationConstants.NEW_APPLICANTS, 1, True
        )

        if produce_submission_event:
            ApplicationEventProducer(
                self.request_scope, source_service=SourceServices.API
            ).application_is_submited(created_application.id)
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
                event_producer.application_is_submited(application)
        return created_applications

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        return self.create_many_applications(company_id, job_id, partial_candidates)

    def create_application_from_resume(self, resume: Resume) -> Application:
        # Create an application for this resume
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
        self, company_id: str, job_id: str, application_id: str
    ):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application: Application = application_repo.get(application_id)
        application_repo.delete(application_id)
        self.update_application_counts(
            company_id, job_id, ApplicationConstants.TOTAL_APPLICANTS, 1, False
        )
        if application.application_is_shortlisted:
            self.update_application_counts(
                company_id, job_id, ApplicationConstants.SHORTLISTED_APPLICANTS, 1, False
            )
        if application.application_match_score and application.application_match_score > 70:
            self.update_application_counts(
                company_id, job_id, ApplicationConstants.HIGH_MATCHING_APPLICANTS, 1, False
            )
        if not application.viewed_by_company:
            self.update_application_counts(
                company_id, job_id, ApplicationConstants.NEW_APPLICANTS, 1, False
            )
        return True

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
                    self.delete_application_for_job, company_id, job_id, application.id
                )
        return True

    def company_updates_application_shortlist(
        self, company_id: str, application_id: str, is_adding_to_shortlist: bool
    ):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        response = application_repo.update_fields(
            application_id, application_is_shortlisted=is_adding_to_shortlist
        )
        self.update_application_counts(
            company_id,
            response.job_id,
            ApplicationConstants.SHORTLISTED_APPLICANTS,
            1,
            is_adding_to_shortlist,
        )

        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_shortlists_application(application_id)
        return response

    def company_views_applications(self, company_id: str, application_ids: list[str]):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        first_application: Application = application_repo.get(application_ids[0])
        response = application_repo.update_many(
            {
                application_id: {ApplicationConstants.VIEWED_BY_COMPANY: True}
                for application_id in application_ids
            }
        )
        self.update_application_counts(
            company_id,
            first_application.job_id,
            ApplicationConstants.NEW_APPLICANTS,
            len(application_ids),
            False,
        )
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_views_applications(application_ids)
        return response
