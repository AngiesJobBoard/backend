from ajb.base import RequestScope
from ajb.contexts.companies.jobs.repository import JobRepository, CreateJob, Job


def create_example_jobs(
    company_id: str, request_scope: RequestScope
) -> tuple[Job, Job]:
    repo = JobRepository(request_scope)
    job_1 = repo.create(CreateJob(company_id=company_id, position_title="Test Job"))
    job_2 = repo.create(CreateJob(company_id=company_id, position_title="Test Job 2"))
    return job_1, job_2
