import base64
from datetime import datetime
from unittest.mock import patch
from ajb.contexts.applications.events import IngressEvent
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.companies.api_ingress_webhooks.models import (
    CreateCompanyAPIIngress,
    IngressSourceType,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.models import (
    RawIngressApplication,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    RawIngressApplicationRepository,
)
from ajb.fixtures.companies import CompanyFixture
from transformers.incoming.postcardmania import IncomingPostCardManiaTransformer
from transformers.router import route_transformer_request


def test_postcardmania_transformer(request_scope):
    # Create company & job
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    raw_ingress_repo = RawIngressApplicationRepository(request_scope)
    api_ingress_repo = CompanyAPIIngressRepository(request_scope, company.id)
    application_repo = ApplicationRepository(request_scope)
    job = company_fixture.create_company_job(company.id)

    # Prepare mock data
    contact_info = {
        "job_name": "Software Engineer",
        "full_name": {"first_name": "Apply", "last_name": "Guy"},
        "email": "applyguy@example.com",
        "city": "Tampa",
        "state": "FL",
        "zip": "33602",
        "prior_application_details": "None",
        "conviction_details": "N/A",
        "terminated": "No",
        "terminated_details": "None",
        "drivers_license_num": "12345678",
        "drivers_license_state": "FL",
        "drivers_license_issued": "2024-06-20",
    }

    # Encode mock data
    resume_data = ["Example resume content"]
    encoded_resume_data = [
        base64.b64encode(data.encode("utf-8")).decode("utf-8") for data in resume_data
    ]

    # Create raw ingress application
    ingress_application = RawIngressApplication(
        id="1",
        ingress_id="123",
        company_id=company.id,
        application_id=None,
        resume_bytes=encoded_resume_data,
        contact_information=contact_info,
        data={
            "contact_information": contact_info,
            "resume_bytes": encoded_resume_data,
            "field1": "value1",
            "field2": "value2",
        },
        created_at=datetime.now(),
        created_by="test_user",
        updated_at=datetime.now(),
        updated_by="test_user",
    )

    raw_ingress_repo.create(
        data=ingress_application, overridden_id="1"
    )  # Add to repository

    # Add to API ingress repo
    api_ingress_data = CreateCompanyAPIIngress(
        integration_name="test",
        source_type=IngressSourceType.COMPANY_WEBSITE,
        source="PostCardMania Website",
        company_id=company.id,
        secret_key="123",
        salt="456",
        expected_jwt="n/a",
        allowed_ips=[],
    )
    api_ingress_record = api_ingress_repo.create(data=api_ingress_data)

    # Patch google maps APIs to avoid error
    maps_patcher = patch("ajb.common.models.get_google_string", return_value=None)
    maps_patcher.start()

    # Run postcardmania transformer via the router
    assert (
        raw_ingress_repo.get(ingress_application.id).application_id is None
    )  # Assert that ingress application hasn't been processed into an application yet

    ingress_event = IngressEvent(
        company_id=company.id, ingress_id=api_ingress_record.id, raw_ingress_data_id="1"
    )
    route_transformer_request(request_scope, ingress_event)

    # Get new application object and test it
    new_application_id = raw_ingress_repo.get(
        ingress_application.id
    ).application_id  # Get id of new application
    assert isinstance(
        new_application_id, str
    )  # Ingress application should now be processed into a new application
    retrieved_application = application_repo.get(new_application_id)

    assert (
        retrieved_application.job_id == job.id
    )  # Application should now be assigned to the Software Engineer job
    assert (
        retrieved_application.name == "Apply Guy"
    )  # Name should have been pulled from the contact information
    assert (
        retrieved_application.email == "applyguy@example.com"
    )  # Email should also have been pulled from the contact info
    assert (
        retrieved_application.extracted_resume_text == "Example resume content"
    )  # Resume content should have been pulled from the bytes data

    # Test create application from data
    transformer = IncomingPostCardManiaTransformer(request_scope, ingress_application)
    transformer.infer_job_from_raw_data()
    transformed_application = transformer.create_application_from_data()
    assert (
        transformed_application.job_id == job.id
    )  # Application should now be assigned to the Software Engineer job
    assert (
        transformed_application.name == "Apply Guy"
    )  # Name should have been pulled from the contact information
    assert (
        transformed_application.email == "applyguy@example.com"
    )  # Email should also have been pulled from the contact info

    # Cleanup
    maps_patcher.stop()
