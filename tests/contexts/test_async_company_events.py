import pytest

from ajb.base.events import BaseKafkaMessage, KafkaTopic
from ajb.contexts.companies.asynchronous_events import AsynchronousCompanyEvents
from ajb.contexts.companies.events import (
    RecruiterAndApplication,
    RecruiterAndApplications,
    RecruiterAndCandidate,
    RecruiterAndCandidates,
)
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaInsightsFactory,
    AlgoliaClientFactory,
    AlgoliaIndex,
)
from ajb.contexts.users.notifications.repository import UserNotificationRepository
from ajb.contexts.companies.actions.repository import CompanyActionRepository

from ajb.fixtures.applications import ApplicationFixture


@pytest.mark.asyncio
async def test_company_is_created(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.user_id = application_data.user.id
    mock_algolia = AlgoliaClientFactory._return_mock()
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_is_created",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=application_data.company.model_dump(mode="json"),
    )
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
        search_companies=AlgoliaSearchRepository(AlgoliaIndex.COMPANIES, mock_algolia),
    ).company_is_created()

    # Check company exists in Algolia
    assert mock_algolia.index.local_items.get(application_data.company.id) is not None


@pytest.mark.asyncio
async def test_company_is_deleted(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    mock_algolia = AlgoliaClientFactory._return_mock()

    # Add company to Algolia
    mock_algolia.index.local_items[
        application_data.company.id
    ] = application_data.company.model_dump()

    # Send delete message
    delete_message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_is_created",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data={"company_id": application_data.company.id},
    )
    await AsynchronousCompanyEvents(
        message=delete_message,
        request_scope=request_scope,
        search_companies=AlgoliaSearchRepository(AlgoliaIndex.COMPANIES, mock_algolia),
    ).company_is_deleted()

    # Check company is deleted from Algolia
    assert mock_algolia.index.local_items.get(application_data.company.id) is None


@pytest.mark.asyncio
async def test_company_is_updated(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    mock_algolia = AlgoliaClientFactory._return_mock()

    # Add company to Algolia
    mock_algolia.index.local_items[
        application_data.company.id
    ] = application_data.company.model_dump()

    # Send update message
    updated_company = application_data.company.model_copy()
    updated_company.name = "Updated Company Name"
    update_message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_is_updated",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=updated_company.model_dump(mode="json"),
    )
    await AsynchronousCompanyEvents(
        message=update_message,
        request_scope=request_scope,
        search_companies=AlgoliaSearchRepository(AlgoliaIndex.COMPANIES, mock_algolia),
    ).company_is_updated()

    # Check company is updated in Algolia
    assert (
        mock_algolia.index.local_items[application_data.company.id]["name"]
        == "Updated Company Name"
    )


@pytest.mark.asyncio
async def test_company_views_applications(request_scope):
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_is_updated",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndApplications(
            company_id="test_company_id",
            applications_and_positions=[
                ("test_application_id", 0),
                ("test_application_id_2", 1),
            ],
        ).model_dump(mode="json"),
    )
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_views_applications()

    # Assert 2 company actions are created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 2
    assert len(company_actions) == 2


@pytest.mark.asyncio
async def test_company_clicks_on_application(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_clicks_on_application",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndApplication(
            company_id=application_data.company.id,
            application_id=application_data.application.id,
        ).model_dump(mode="json"),
    )
    request_scope.user_id = application_data.user.id
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_clicks_on_application()

    # Assert 1 company action is created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 1
    assert len(company_actions) == 1

    # Assert 1 user notification is created
    notifications, count = UserNotificationRepository(
        request_scope, application_data.user.id
    ).query()
    assert count == 1
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_company_shortlists_application(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.user_id = application_data.user.id
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_shortlists_application",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndApplication(
            company_id=application_data.company.id,
            application_id=application_data.application.id,
        ).model_dump(mode="json"),
    )
    request_scope.user_id = application_data.user.id
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_shortlists_application()

    # Assert 1 company action is created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 1
    assert len(company_actions) == 1

    # Assert 1 user notification is created
    notifications, count = UserNotificationRepository(
        request_scope, application_data.user.id
    ).query()
    assert count == 1
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_company_rejects_application(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_rejects_application",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndApplication(
            company_id=application_data.company.id,
            application_id=application_data.application.id,
        ).model_dump(mode="json"),
    )
    request_scope.user_id = application_data.user.id
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_rejects_application()

    # Assert 1 company action is created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 1
    assert len(company_actions) == 1

    # Assert 1 user notification is created
    notifications, count = UserNotificationRepository(
        request_scope, application_data.user.id
    ).query()
    assert count == 1
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_company_views_candidates(request_scope):
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_views_candidates",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndCandidates(
            company_id="test_company_id",
            candidates_and_positions=[
                ("test_user_id", 0),
                ("test_user_id_2", 1),
            ],
        ).model_dump(mode="json"),
    )
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_views_candidates()

    # Assert 2 company actions are created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 2
    assert len(company_actions) == 2


@pytest.mark.asyncio
async def test_company_clicks_candidate(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_clicks_candidate",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndCandidate(
            company_id=application_data.company.id,
            candidate_id=application_data.user.id,
        ).model_dump(mode="json"),
    )
    request_scope.user_id = application_data.user.id

    mock_insights = AlgoliaInsightsFactory._return_mock()
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
        candidate_insights=AlgoliaInsightsRepository(
            AlgoliaIndex.CANDIDATES, mock_insights
        ),
    ).company_clicks_candidate()

    # Assert 1 company action is created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 1
    assert len(company_actions) == 1

    # Assert 1 candidate insight is created
    assert len(mock_insights.sent_events) == 1


@pytest.mark.asyncio
async def test_company_saves_candidate(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    message = BaseKafkaMessage(
        topic=KafkaTopic.COMPANIES,
        event_type="company_saves_candidate",
        source_service="api",
        requesting_user_id=request_scope.user_id,
        data=RecruiterAndCandidate(
            company_id=application_data.company.id,
            candidate_id=application_data.user.id,
        ).model_dump(mode="json"),
    )
    request_scope.user_id = application_data.user.id
    request_scope.company_id = application_data.company.id
    await AsynchronousCompanyEvents(
        message=message,
        request_scope=request_scope,
    ).company_saves_candidate()

    # Assert 1 company action is created
    company_actions, count = CompanyActionRepository(request_scope).query()
    assert count == 1
    assert len(company_actions) == 1

    # Assert 1 user notification is created
    notifications, count = UserNotificationRepository(
        request_scope, application_data.user.id
    ).query()
    assert count == 1
    assert len(notifications) == 1
