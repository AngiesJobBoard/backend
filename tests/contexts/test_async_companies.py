import pytest

from ajb.contexts.companies.email_ingress_webhooks.repository import (
    CompanyEmailIngressRepository,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.base.events import BaseKafkaMessage, KafkaTopic, CompanyEvent
from ajb.vendor.sendgrid.client_factory import SendgridFactory
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.fixtures.users import UserFixture
from ajb.fixtures.companies import CompanyFixture
from services.resolvers.companies import CompanyEventsResolver


@pytest.fixture
def mock_sendgrid():
    client = SendgridFactory._return_mock()
    yield SendgridRepository(client)  # type: ignore


@pytest.mark.asyncio
async def test_async_company_creation(request_scope, mock_sendgrid):
    created_user = UserFixture(request_scope).create_user()
    created_company = CompanyFixture(request_scope).create_company()

    request_scope.user_id = created_user.id
    message = BaseKafkaMessage(
        requesting_user_id=created_user.id,
        data=created_company.model_dump(mode="json"),
        topic=KafkaTopic.COMPANIES,
        event_type=CompanyEvent.COMPANY_IS_CREATED,
        source_service="test",
    )
    await CompanyEventsResolver(
        message=message, request_scope=request_scope, sendgrid=mock_sendgrid
    ).company_is_created()

    # Check that the email was sent
    assert len(mock_sendgrid.client.sent_emails) == 1

    # Check that the subdomain relationships were created
    email_ingress_repo = CompanyEmailIngressRepository(
        request_scope, created_company.id
    )
    results, _ = email_ingress_repo.query()
    assert len(results) == 1

    # Check that the API ingress relationship was created
    api_ingress_repo = CompanyAPIIngressRepository(request_scope, created_company.id)
    assert api_ingress_repo.get_all() is not None
