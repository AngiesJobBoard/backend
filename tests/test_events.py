from ajb.base.events import SourceServices, KafkaTopic
from ajb.contexts.users.events import UserEventProducer
from ajb.contexts.companies.events import CompanyEventProducer

from ajb.fixtures.users import UserFixture
from ajb.fixtures.companies import CompanyFixture


def test_user_event_producer(request_scope):
    user_event_producer = UserEventProducer(request_scope, SourceServices.API)
    created_user = UserFixture(request_scope).create_user()
    user_event_producer.user_created_event(created_user)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 1


def test_company_event_producer(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    company_event_producer = CompanyEventProducer(request_scope, SourceServices.API)

    company_event_producer.company_created_event(company)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 1

    company_event_producer.company_views_applications(
        application_ids=[],
        search_page=1,
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 2

    company_event_producer.company_clicks_on_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 3

    company_event_producer.company_shortlists_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 4

    company_event_producer.company_rejects_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 5
