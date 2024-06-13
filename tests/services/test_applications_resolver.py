import asyncio
from unittest.mock import patch

from ajb.base.events import BaseKafkaMessage
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.usecase.application_usecase import ApplicationUseCase
from ajb.fixtures.companies import CompanyFixture
from services.resolvers.applications import (
    ApplicationEventsResolver,
    CouldNotParseResumeText,
)

from ajb.config.settings import SETTINGS


def test_upload_resume(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    # Create application
    application_repository = ApplicationRepository(request_scope)
    application_usecase = ApplicationUseCase(request_scope)
    application = CreateApplication(
        company_id=company.id,
        job_id=job.id,
        name=None,
        email="johndoe@applicant.com",
    )

    created_application = application_usecase.create_application(
        company.id, job.id, application
    )

    assert application_repository.get(created_application.id).name is None

    # Create resolver
    resolver = ApplicationEventsResolver(
        BaseKafkaMessage(
            data={
                "company_id": company.id,
                "job_id": job.id,
                "application_id": created_application.id,
                "resume_id": "1",
            },
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
    )

    # Add extracted text field to application
    application_repository.update_fields(
        created_application.id, extracted_resume_text="Example resume text"
    )

    # Run upload_resume
    example_resume = ExtractedResume(first_name="Apply", last_name="Guy")
    with patch( # Patch the AI resume extractor with this example one
        "ajb.contexts.applications.extract_data.usecase.ResumeExtractorUseCase.extract_resume_information",
        return_value=example_resume,
    ):
        asyncio.run(resolver.upload_resume())

    # Assertions
    assert application_repository.get(created_application.id).name == "Apply Guy" # The application name should be pulled in from the resume now