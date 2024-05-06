from ajb.base import BaseUseCase, Collection

from migrations.base import MIGRATION_REQUEST_SCOPE


class MarkJobsActive(BaseUseCase):
    def run(self):
        job_repo = self.get_repository(Collection.JOBS)
        all_jobs = job_repo.get_all()

        for job in all_jobs:
            job_repo.update_fields(job.id, active=True)


def main():
    MarkJobsActive(MIGRATION_REQUEST_SCOPE).run()
