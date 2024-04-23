from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.models import Company
from ajb.contexts.companies.recruiters.models import Recruiter

from migrations.base import MIGRATION_REQUEST_SCOPE


class DeleteMultipleRecruitersMigration(BaseUseCase):
    """
    This checks for all jobs and applications of various states for all companies and updates the company counts accordingly
    """

    def get_all_companies(self) -> list[Company]:
        company_repo = self.get_repository(Collection.COMPANIES)
        return company_repo.get_all()

    def delete_duplicate_recruiters(self, company_id: str):
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        all_recruiters: list[Recruiter] = recruiter_repo.get_all(company_id=company_id)
        seen_recruiter_ids = []
        for recruiter in all_recruiters:
            if recruiter.user_id not in seen_recruiter_ids:
                seen_recruiter_ids.append(recruiter.user_id)
            else:
                recruiter_repo.delete(recruiter.id)
                print(f"Deleted recruiter: {recruiter.id}")

    def run(self):
        companies = self.get_all_companies()
        for company in companies:
            self.delete_duplicate_recruiters(company.id)


def main():
    DeleteMultipleRecruitersMigration(MIGRATION_REQUEST_SCOPE).run()
