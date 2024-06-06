from email.message import Message

from ajb.base import (
    BaseUseCase,
    Collection,
    RequestScope,
)
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.base.events import SourceServices
from ajb.common.models import ApplicationQuestion
from ajb.contexts.resumes.usecase import ResumeUseCase
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.models import (
    CreateApplicationStatusUpdate,
    CompanyApplicationView,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.recruiter_updates.usecase import RecruiterUpdatesUseCase
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from ajb.contexts.billing.usecase import (
    CompanyBillingUsecase,
    UsageType,
)
from ajb.contexts.applications.extract_data.ai_extractor import (
    SyncronousAIResumeExtractor,
)
from ajb.vendor.pdf_plumber import extract_text
from ajb.vendor.arango.repository import ArangoDBRepository

from ajb.contexts.applications.models import (
    CreateApplication,
    Application,
    ScanStatus,
    CompanyApplicationStatistics,
)
from ajb.contexts.applications.constants import ApplicationConstants


class ApplicationUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        self.request_scope = request_scope
        self.storage_repo = storage or FirebaseStorageRepository()

    def _get_job_questions(self, job_id: str) -> list[ApplicationQuestion]:
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
            ).company_gets_match_score(
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
                event_producer.company_gets_match_score(company_id, job_id, application)
        return created_applications

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        return self.create_many_applications(company_id, job_id, partial_candidates)

    def create_application_from_resume(
        self,
        data: UserCreateResume,
        additional_partial_data: CreateApplication | None = None,
    ) -> Application:
        # Create an application for this resume
        resume = ResumeUseCase(self.request_scope).create_resume(data)
        partial_application = CreateApplication(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            resume_scan_status=ScanStatus.PENDING,
            match_score_status=ScanStatus.PENDING,
            extracted_resume_text=extract_text(data.resume_data),
        )
        if additional_partial_data:
            partial_application = partial_application.model_dump()
            partial_application.update(additional_partial_data.model_dump())
            partial_application = CreateApplication(**partial_application)

        created_application = self.create_application(
            resume.company_id, resume.job_id, partial_application, False
        )
        # Create kafka event for parsing the resume
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            company_id=resume.company_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
        )
        return created_application

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

    def process_email_application_ingress(
        self,
        ingress_email: Message,
        ingress_record: CompanyEmailIngress,
    ) -> list[Application]:
        created_applications = []
        if not ingress_email.is_multipart():
            raise ValueError("Email is not multipart")
        for part in ingress_email.walk():
            content_disposition = part.get("Content-Disposition")
            if not content_disposition or "attachment" not in content_disposition:
                continue
            if not ingress_record.job_id:
                continue
            created_application = self.create_application_from_resume(
                UserCreateResume(
                    file_type=part.get_content_type(),
                    file_name=str(part.get_filename()),
                    resume_data=part.get_payload(decode=True),  # type: ignore
                    company_id=ingress_record.company_id,
                    job_id=ingress_record.job_id,
                )
            )
            created_applications.append(created_application)

        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=ingress_record.company_id,
            incremental_usages={
                UsageType.EMAIL_INGRESS: len(created_applications),
            },
        )
        return created_applications

    def application_is_created_from_raw_text(
        self, company_id: str, job_id: str, raw_text: str
    ):
        partial_application = CreateApplication(
            company_id=company_id,
            job_id=job_id,
            name="-",
            email="-",
            match_score_status=ScanStatus.STARTED,
            extracted_resume_text=raw_text,
        )
        partial_application.application_questions = self._get_job_questions(job_id)
        created_application = self.create_application(
            company_id, job_id, partial_application, False
        )
        resume_information = (
            SyncronousAIResumeExtractor().get_candidate_profile_from_resume_text(
                raw_text
            )
        )
        application_repo: ApplicationRepository = self.get_repository(Collection.APPLICATIONS)  # type: ignore
        application_repo.update_application_with_parsed_information(
            application_id=created_application.id,
            resume_information=resume_information,  # type: ignore
        )

        # Create kafka event for handling the match
        ApplicationEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_gets_match_score(
            company_id=company_id,
            job_id=job_id,
            application_id=created_application.id,
        )
        return created_application

    def _get_filter_string(self, job_id: str | None = None):
        filter_string = "FILTER doc.company_id == @_BIND_VAR_0\n"
        if job_id:
            filter_string += " AND doc.job_id == @_BIND_VAR_1\n"
        return filter_string

    def _format_status_summary_query(self, job_id: str | None = None):
        query_string = f"""
        LET statusCounts = (
            FOR doc IN applications
            {self._get_filter_string(job_id)}
            COLLECT application_status = doc.application_status WITH COUNT INTO statusCount
        """
        query_string += "RETURN {application_status, statusCount}\n)"
        return query_string

    def _format_match_score_summary_query(self, job_id: str | None = None):
        query_string = f"""
        LET scoreBuckets = (
            FOR doc IN applications
            {self._get_filter_string(job_id)}
            LET scoreRange = (
                doc.application_match_score <= 30 ? '0-30' :
                doc.application_match_score > 30 && doc.application_match_score <= 70 ? '30-70' :
                doc.application_match_score > 70 ? '70+' :
                'Unknown' // Optional
            )
            COLLECT range = scoreRange WITH COUNT INTO rangeCount
        """
        query_string += "RETURN {range, rangeCount}\n)"
        return query_string

    def get_application_statistics(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> CompanyApplicationStatistics:
        status_query = self._format_status_summary_query(job_id)
        match_score_query = self._format_match_score_summary_query(job_id)

        full_query_string = ""
        full_query_string += status_query
        full_query_string += match_score_query
        full_query_string += "\nRETURN {statusCounts, scoreBuckets}"
        bind_vars = {"_BIND_VAR_0": company_id}
        if job_id:
            bind_vars["_BIND_VAR_1"] = job_id

        repo = ArangoDBRepository(self.request_scope.db, Collection.APPLICATIONS)
        res = repo.execute_custom_statement(full_query_string, bind_vars)
        return CompanyApplicationStatistics.from_arango_query(res)
