from ajb.base.events import SourceServices, KafkaTopic
from ajb.contexts.users.events import UserEventProducer
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.search.jobs.models import AlgoliaJobSearchResults
from ajb.contexts.search.companies.models import AlgoliaCompanySearchResults
from ajb.contexts.search.candidates.models import AlgoliaCandidateSearchResults

from ajb.fixtures.users import UserFixture
from ajb.fixtures.companies import CompanyFixture


def test_user_event_producer(request_scope):
    user_event_producer = UserEventProducer(request_scope, SourceServices.API)
    created_user = UserFixture(request_scope).create_user()
    user_event_producer.user_created_event(created_user)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 1

    user_event_producer.user_delete_event(created_user.id)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 2

    user_event_producer.user_is_updated(created_user)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 3

    user_event_producer.user_views_jobs(
        AlgoliaJobSearchResults(
            hits=[],
            nbHits=0,
            page=0,
            nbPages=0,
            hitsPerPage=0,
            exhaustiveNbHits=True,
        ),
        search_page=1,
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 4

    user_event_producer.user_clicks_job(
        company_id="abc",
        job_id="def",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 5

    user_event_producer.user_saves_job(
        company_id="abc",
        job_id="def",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 6

    user_event_producer.user_applies_job(
        company_id="abc", job_id="def", application_id="ghi", resume_id="jkl"
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 7

    user_event_producer.user_views_companies(
        AlgoliaCompanySearchResults(
            hits=[],
            nbHits=0,
            page=0,
            nbPages=0,
            hitsPerPage=0,
            exhaustiveNbHits=True,
        ),
        search_page=1,
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 8

    user_event_producer.user_clicks_company(
        company_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 9

    user_event_producer.user_saves_company(
        company_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 10


def test_company_event_producer(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    company_event_producer = CompanyEventProducer(request_scope, SourceServices.API)

    company_event_producer.company_created_event(company)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 1

    company_event_producer.company_delete_event(company.id)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 2

    company_event_producer.company_is_updated(company)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 3

    company_event_producer.company_views_applications(
        application_ids=[],
        search_page=1,
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 4

    company_event_producer.company_clicks_on_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 5

    company_event_producer.company_shortlists_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 6

    company_event_producer.company_rejects_application(
        application_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 7

    company_event_producer.company_views_candidates(
        AlgoliaCandidateSearchResults(
            hits=[],
            nbHits=0,
            page=0,
            nbPages=0,
            hitsPerPage=0,
            exhaustiveNbHits=True,
        ),
        search_page=1,
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 8

    company_event_producer.company_clicks_candidate(
        candidate_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 9

    company_event_producer.company_saves_candidate(
        candidate_id="abc",
    )
    assert len(request_scope.kafka_producer.messages[KafkaTopic.COMPANIES.value]) == 10
