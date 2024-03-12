from ajb.base import BaseUseCase, Collection, RepoFilterParams
from ajb.base.events import SourceServices
from ajb.contexts.resumes.models import Resume
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.arango.models import Filter

from .models import CreateApplication, Application, ScanStatus


class ApplicationUseCase(BaseUseCase):

    def _get_job_questions(self, job_id):
        job: Job = self.get_object(Collection.JOBS, job_id)
        return job.application_questions

    def create_application(self, job_id: str, partial_application: CreateApplication) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        partial_application.application_questions = self._get_job_questions(job_id)
        created_application = application_repo.create(partial_application)
        CompanyEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).application_is_submited(created_application.id)
        return created_application
    
    def create_many_applications(
        self,
        job_id: str,
        partial_applications: list[CreateApplication],
    ) -> list[str]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        job_questions = self._get_job_questions(job_id)
        candidates_with_job_questions = []
        for candidate in partial_applications:
            candidate.application_questions = job_questions
            candidates_with_job_questions.append(candidate)
        return application_repo.create_many(candidates_with_job_questions)

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        created_applications = self.create_many_applications(job_id, partial_candidates)
        event_producter = CompanyEventProducer(self.request_scope, SourceServices.API)
        for application in created_applications:
            event_producter.application_is_submited(application)
        return created_applications

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
        created_application = self.create_application(resume.job_id, partial_application)

        # Create kafka event for parsing the resume
        CompanyEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
        )
        return created_application

    def delete_all_applications_for_job(self, company_id: str, job_id: str):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        applications = application_repo.query(
            repo_filters=RepoFilterParams(
                filters=[
                    Filter(field="company_id", value=company_id),
                    Filter(field="job_id", value=job_id),
                ]
            )
        )[0]
        application_repo.delete_many([application.id for application in applications])
        return True
