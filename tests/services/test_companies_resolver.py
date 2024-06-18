import asyncio
from unittest.mock import patch
from ajb.base.events import BaseKafkaMessage
from ajb.config.settings import SETTINGS
from ajb.contexts.companies.jobs.job_score.ai_job_score import JobScore
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.repository import CompanyRepository
from ajb.fixtures.companies import CompanyFixture
from services.resolvers.companies import CompanyEventsResolver


def test_company_job_resolvers(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)
    job = company_fixture.create_company_job(company.id)

    # Create resolver object
    resolver = CompanyEventsResolver(
        BaseKafkaMessage(
            data={
                "company_id": company.id,
                "job_id": job.id,
            },
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
    )

    # Run company creates job method
    mock_return_value = JobScore(job_score=99, job_score_reason="Example reason")
    with patch(
        "ajb.contexts.companies.jobs.job_score.ai_job_score.AIJobScore.get_job_score",
        return_value=mock_return_value,
    ):
        asyncio.run(resolver.company_creates_job())

    # Validate job creation
    retrieved_job = job_repo.get(job.id)
    retrieved_company = company_repo.get(company.id)
    assert retrieved_job.job_score == 99  # Check that the job score was updated
    assert (
        retrieved_job.job_score_reason == "Example reason"
    )  # Check for new job score reason
    assert (
        retrieved_company.total_jobs == 1
    )  # Company job counter should've been incremented

    # Test updating job with a lower score
    mock_return_value = JobScore(job_score=87, job_score_reason="Updated reason")
    with patch(
        "ajb.contexts.companies.jobs.job_score.ai_job_score.AIJobScore.get_job_score",
        return_value=mock_return_value,
    ):
        asyncio.run(resolver.company_updates_job())

    # Validate job updates
    retrieved_job = job_repo.get(job.id)
    assert retrieved_job.job_score == 87  # Check that the job score was updated again
    assert (
        retrieved_job.job_score_reason == "Updated reason"
    )  # Check for the updated job score reason
