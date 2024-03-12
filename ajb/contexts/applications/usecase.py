from ajb.base import BaseUseCase, Collection, RepoFilterParams
from ajb.base.events import SourceServices
from ajb.contexts.resumes.models import Resume
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.vendor.arango.models import Filter

from .models import CreateApplication, Application, ScanStatus


class ApplicationUseCase(BaseUseCase):
    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        created_applications = application_repo.create_many(candidates)

        # Create a company event for each application created to perform the match
        event_producter = CompanyEventProducer(self.request_scope, SourceServices.API)
        for application in created_applications:
            event_producter.application_is_submited(application)
        return created_applications

    def create_application_from_resume(self, resume: Resume) -> Application:
        # Create an application for this resume
        application_repo = self.get_repository(Collection.APPLICATIONS)
        created_application = application_repo.create(
            CreateApplication(
                company_id=resume.company_id,
                job_id=resume.job_id,
                resume_id=resume.id,
                name="Resume Scan Pending",
                email="Resume Scan Pending",
                resume_scan_status=ScanStatus.PENDING,
                match_score_status=ScanStatus.PENDING,
            )
        )

        # Create kafka event for parsing the resume
        CompanyEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).company_uploads_resume(
            job_id=resume.job_id,
            resume_id=resume.id,
            application_id=created_application.id,
        )
        return created_application

    def create_application_from_data(
        self, application: CreateApplication
    ) -> Application:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        created_application = application_repo.create(application)
        CompanyEventProducer(
            self.request_scope, source_service=SourceServices.API
        ).application_is_submited(created_application.id)
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
