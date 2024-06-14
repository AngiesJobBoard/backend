import asyncio
from unittest.mock import patch

from ajb.base.events import BaseKafkaMessage
from ajb.common.models import AnswerEnum, ApplicationQuestion, Location, QuestionStatus
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.applications.matching.ai_matching import ApplicantMatchScore
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.usecase.application_usecase import ApplicationUseCase
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.repository import CompanyRepository
from ajb.fixtures.companies import CompanyFixture
from services.resolvers.applications import (
    ApplicationEventsResolver,
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
    with patch(  # Patch the AI resume extractor with this example one
        "ajb.contexts.applications.extract_data.usecase.ResumeExtractorUseCase.extract_resume_information",
        return_value=example_resume,
    ):
        asyncio.run(resolver.upload_resume())

    # Assertions
    assert (
        application_repository.get(created_application.id).name == "Apply Guy"
    )  # The application name should be pulled in from the resume now


def test_company_gets_match_score(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    # Create application
    application_repository = ApplicationRepository(request_scope)
    application_usecase = ApplicationUseCase(request_scope)
    application = CreateApplication(
        company_id=company.id,
        job_id=job.id,
        name=None,
        email="applyguy@applicant.com",
    )

    created_application = application_usecase.create_application(
        company.id, job.id, application
    )

    # Create applicant events resolver
    resolver = ApplicationEventsResolver(
        BaseKafkaMessage(
            data={
                "company_id": company.id,
                "job_id": job.id,
                "application_id": created_application.id,
            },
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
    )

    # Run the resolver get match score method
    with patch(  # Patch the AI matcher to give our applicant a match score
        "ajb.contexts.applications.matching.ai_matching.AIApplicationMatcher.get_match_score",
        return_value=ApplicantMatchScore(
            match_score=99, match_reason="Apply guy is the best."
        ),
    ):
        asyncio.run(resolver.company_gets_match_score())

    # Assert match score & high matching applicants
    assert (
        application_repository.get(created_application.id).application_match_score == 99
    )
    assert company_repo.get(company.id).high_matching_applicants == 1
    assert job_repo.get(job.id).high_matching_applicants == 1


def test_extract_application_filters(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    job_repo = JobRepository(request_scope, company.id)

    # Add a location to the job
    job.location_override = Location(lat=36.4635, lng=138.969)
    job_repo.update(job.id, job)

    # Create application
    application_repository = ApplicationRepository(request_scope)
    application_usecase = ApplicationUseCase(request_scope)
    application = CreateApplication(
        company_id=company.id,
        job_id=job.id,
        name=None,
        email="applyguy@applicant.com",
        user_location=Location(lat=36.478, lng=138.879),
    )

    created_application = application_usecase.create_application(
        company.id, job.id, application
    )

    # Create applicant events resolver
    resolver = ApplicationEventsResolver(
        BaseKafkaMessage(
            data={
                "company_id": company.id,
                "job_id": job.id,
                "application_id": created_application.id,
            },
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
    )

    # Run extract application filters method
    with patch(  # Patch the Google Maps API call
        "ajb.contexts.applications.models.Application.applicant_is_in_same_state_as_job",
        return_value=True,
    ):
        asyncio.run(resolver.extract_application_filters())

    # Check application filters
    retrieved_application = application_repository.get(created_application.id)
    assert (
        retrieved_application.additional_filters.in_same_state_as_location == True
    )  # Validate that the patched result was saved to filters
    assert (
        retrieved_application.additional_filters.miles_between_job_and_applicant == 8
    )  # Validate distance between two given locations is correct


def test_answer_application_questions(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    # Add job questions
    job_repo.update_fields(
        job.id, application_questions_as_strings=["Do you like Python?"]
    )

    # Create application
    application_repository = ApplicationRepository(request_scope)
    application_usecase = ApplicationUseCase(request_scope)

    application = CreateApplication(
        company_id=company.id,
        job_id=job.id,
        name=None,
        email="applyguy@applicant.com",
        user_location=Location(lat=36.478, lng=138.879),
    )

    created_application = application_usecase.create_application(
        company.id, job.id, application
    )

    # Create applicant events resolver
    resolver = ApplicationEventsResolver(
        BaseKafkaMessage(
            data={
                "company_id": company.id,
                "job_id": job.id,
                "application_id": created_application.id,
            },
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
    )

    # Prepare data
    patched_json = {  # JSON response to be patched in place of an OpenAI call
        "answer": "Yes",
        "confidence": 9,
        "reasoning": "Python is the best.",
    }

    # Run the answer application questions method
    with patch(  # Patch the OpenAI call
        "ajb.vendor.openai.repository.AsyncOpenAIRepository.json_prompt",
        return_value=patched_json,
    ):
        asyncio.run(resolver.answer_application_questions())

    # Assertions here
    retrieved_app = application_repository.get(created_application.id)
    assert (
        len(retrieved_app.application_questions) == 1
    )  # There should be 1 application question
    assert (
        retrieved_app.application_questions[0].question_status
        == QuestionStatus.ANSWERED
    )  # The question should now be answered
    assert (
        retrieved_app.application_questions[0].answer == AnswerEnum.YES
    )  # Who doesn't love Python?
    assert (
        retrieved_app.application_questions[0].confidence == 9
    )  # The confidence be equal to the passed in value of 9
    assert (
        retrieved_app.application_questions[0].reasoning == patched_json["reasoning"]
    )  # The reasoning should reflect the response from the patched JSON
