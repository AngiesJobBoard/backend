"""
We already ran into a case where someone made a company then another employee also made the company.

This is a migration to handle this situation by forcing 1 companie's data to merge with the other then deleting the other company.

... This will get complicated as more data is produced under a company...
"""

from ajb.base import BaseUseCase, Collection
from migrations.base import MIGRATION_REQUEST_SCOPE
from migrations.company_job_counts import CompanyCountsMigrationUseCase


class CompanyMergeMigrator(BaseUseCase):
    def merge_company_jobs(self, from_company_id: str, to_company_id: str):
        job_repo = self.get_repository(Collection.JOBS)
        all_from_company_jobs = job_repo.get_all(company_id=from_company_id)
        print(f"Jobs from company {from_company_id}: {len(all_from_company_jobs)}")
        for job in all_from_company_jobs:
            job_repo.update_fields(job.id, company_id=to_company_id)
    
    def merge_company_recruiters(self, from_company_id: str, to_company_id: str):
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        all_from_company_recruiters = recruiter_repo.get_all(company_id=from_company_id)
        all_to_company_recruiters = recruiter_repo.get_all(company_id=to_company_id)
        print(f"Recruiters from company {from_company_id}: {len(all_from_company_recruiters)}")
        for from_recruiter in all_from_company_recruiters:
            # Check that user id of from recruiter doesnt exist in any to recruiters
            if from_recruiter.user_id in [recruiter.user_id for recruiter in all_to_company_recruiters]:
                continue
            recruiter_repo.update_fields(from_recruiter.id, company_id=to_company_id)

    def merge_company_applications(self, from_company_id: str, to_company_id: str):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        all_from_company_applications = application_repo.get_all(company_id=from_company_id)
        print(f"Applications from company {from_company_id}: {len(all_from_company_applications)}")
        for application in all_from_company_applications:
            application_repo.update_fields(application.id, company_id=to_company_id)
    
    def merge_all_resumes(self, from_company_id: str, to_company_id: str):
        resume_repo = self.get_repository(Collection.RESUMES)
        all_from_company_resumes = resume_repo.get_all(company_id=from_company_id)
        print(f"Resumes from company {from_company_id}: {len(all_from_company_resumes)}")
        for resume in all_from_company_resumes:
            resume_repo.update_fields(resume.id, company_id=to_company_id)
        
    
    def merge_company_data(self, from_company_id: str, to_company_id: str):
        self.merge_company_jobs(from_company_id, to_company_id)
        self.merge_company_recruiters(from_company_id, to_company_id)
        self.merge_company_applications(from_company_id, to_company_id)
        self.merge_all_resumes(from_company_id, to_company_id)

        # Now update counts for from and to companys
        company_counts_migration = CompanyCountsMigrationUseCase(MIGRATION_REQUEST_SCOPE)
        from_company = self.get_object(Collection.COMPANIES, from_company_id)
        to_company = self.get_object(Collection.COMPANIES, to_company_id)
        company_counts_migration.update_company_counts(from_company)
        company_counts_migration.update_company_counts(to_company)
    

def main():
    usecase = CompanyMergeMigrator(MIGRATION_REQUEST_SCOPE)
    usecase.merge_company_data("PostcardMania", "postcardmania")
