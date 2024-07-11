from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.models import Company
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.applications.models import Application
from ajb.config.settings import SETTINGS

from migrations.base import MIGRATION_REQUEST_SCOPE


class CompanyCountsMigrationUseCase(BaseUseCase):
    """
    This checks for all jobs and applications of various states for all companies and updates the company counts accordingly
    """

    def get_all_companies(self) -> list[Company]:
        company_repo = self.get_repository(Collection.COMPANIES)
        return company_repo.get_all()

    def get_company_jobs(self, company_id: str) -> list[Job]:
        job_repo = self.get_repository(Collection.JOBS)
        all_jobs = job_repo.get_all(company_id=company_id)
        return [job for job in all_jobs if job.active]

    def get_company_job_applications(self, job_id: str) -> list[Application]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        return application_repo.get_all(job_id=job_id)

    def update_company_counts(self, company: Company):
        company_repo = self.get_repository(Collection.COMPANIES)
        jobs = self.get_company_jobs(company.id)

        total_applicants = 0
        high_matching_applicants = 0
        new_applicants = 0

        for job in jobs:
            applications = self.get_company_job_applications(job.id)
            total_applicants += len(applications)
            for application in applications:
                if (
                    application.application_match_score
                    and application.application_match_score
                    >= SETTINGS.DEFAULT_HIGH_MATCH_THRESHOLD
                ):
                    high_matching_applicants += 1

                if not application.application_status:
                    new_applicants += 1

        updated_company: Company = company_repo.update_fields(
            company.id,
            total_jobs=len(jobs),
            total_applicants=total_applicants,
            high_matching_applicants=high_matching_applicants,
            new_applicants=new_applicants,
        )
        print(f"Company: {company.id}, {company.name}")
        print(
            f"Original Counts: {company.total_jobs}, {company.total_applicants}, {company.high_matching_applicants}, {company.new_applicants}"
        )
        print(
            f"Updated Counts: {updated_company.total_jobs}, {updated_company.total_applicants}, {updated_company.high_matching_applicants}, {updated_company.new_applicants}\n"
        )

    def run(self):
        companies = self.get_all_companies()
        for company in companies:
            self.update_company_counts(company)


class JobCountsMigrationUseCase(BaseUseCase):
    def get_all_jobs(self) -> list[Job]:
        job_repo = self.get_repository(Collection.JOBS)
        return job_repo.get_all()

    def get_job_applications(self, job_id: str) -> list[Application]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        return application_repo.get_all(job_id=job_id)

    def update_job_counts(self, job: Job):
        job_repo = self.get_repository(Collection.JOBS)
        applications = self.get_job_applications(job.id)

        high_matching_applicants = 0
        new_applicants = 0

        for application in applications:
            if (
                application.application_match_score
                and application.application_match_score
                >= SETTINGS.DEFAULT_HIGH_MATCH_THRESHOLD
            ):
                high_matching_applicants += 1

            if not application.application_status:
                new_applicants += 1

        updated_job: Job = job_repo.update_fields(
            job.id,
            total_applicants=len(applications),
            high_matching_applicants=high_matching_applicants,
            new_applicants=new_applicants,
        )
        print(f"Job: {job.id}, {job.position_title}")
        print(
            f"Original Counts: {job.total_applicants}, {job.high_matching_applicants}, {job.new_applicants}"
        )
        print(
            f"Updated Counts: {updated_job.total_applicants}, {updated_job.high_matching_applicants}, {updated_job.new_applicants}\n"
        )

    def run(self):
        jobs = self.get_all_jobs()
        for job in jobs:
            self.update_job_counts(job)


def main():
    CompanyCountsMigrationUseCase(MIGRATION_REQUEST_SCOPE).run()
    JobCountsMigrationUseCase(MIGRATION_REQUEST_SCOPE).run()


if __name__ == "__main__":
    main()
