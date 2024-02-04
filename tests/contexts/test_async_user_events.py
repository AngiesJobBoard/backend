import json
import pytest

from ajb.base.events import BaseKafkaMessage, KafkaTopic
from ajb.contexts.users.asynchronous_events import AsynchronousUserEvents
from ajb.contexts.users.events import (
    UserJobAndApplication,
    UserAndJobs,
    UserAndJob,
    UserAndCompanies,
    UserAndCompany,
)
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaInsightsFactory,
    AlgoliaClientFactory,
    AlgoliaIndex,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.companies.notifications.repository import (
    CompanyNotificationRepository,
)
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.users.actions.repository import UserActionRepository
from ajb.vendor.openai.repository import OpenAIRepository, OpenAIClientFactory
from ajb.vendor.sendgrid.repository import SendgridRepository, SendgridFactory
from ajb.contexts.users.usecase import UserUseCase

from ajb.fixtures.applications import ApplicationFixture
from ajb.fixtures.users import UserFixture


@pytest.mark.asyncio
async def test_user_application_event(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_applies_to_job",
        source_service="api",
        requesting_user_id=application_data.user.id,
        data=UserJobAndApplication(
            user_id=application_data.user.id,
            company_id=application_data.job.company_id,
            job_id=application_data.job.id,
            application_id=application_data.application.id,
            resume_id=application_data.resume.id,
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )
    mock_algolia = AlgoliaClientFactory._return_mock()
    mock_insights = AlgoliaInsightsFactory._return_mock()
    mock_openai = OpenAIClientFactory._return_mock(
        return_content=json.dumps({"match_score": 2, "match_reason": "test"})
    )
    mock_sendgrid = SendgridFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        search_candidates=AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES, mock_algolia
        ),
        job_insights=AlgoliaInsightsRepository(AlgoliaIndex.JOBS, mock_insights),
        company_insights=AlgoliaInsightsRepository(
            AlgoliaIndex.COMPANIES, mock_insights
        ),
        openai=OpenAIRepository(mock_openai),  # type: ignore
        sendgrid=SendgridRepository(mock_sendgrid),  # type: ignore
    ).user_applies_to_job()

    # Assert matching results are applied to application
    application = ApplicationRepository(request_scope).get(
        application_data.application.id
    )
    assert application.application_match_score == 2
    assert application.application_match_reason == "test"

    # Assert algolia insights event is sent
    assert len(mock_insights.sent_events) == 1

    # Assert notification is sent to company
    company_notification_repo = CompanyNotificationRepository(
        request_scope, application_data.company.id
    )
    (
        all_company_notifications,
        count,
    ) = company_notification_repo.get_unread_notifications()
    assert count == 1
    assert len(all_company_notifications) == 1
    assert (
        all_company_notifications[0].title == "New application for Software Engineer!"
    )
    assert all_company_notifications[0].is_read is False

    # Assert recruiter is sent email
    assert len(mock_sendgrid.sent_emails) == 1
    assert (
        str(mock_sendgrid.sent_emails[0]["subject"])
        == "New Application for Software Engineer!"
    )


@pytest.mark.asyncio
async def test_new_user_event(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_is_created",
        source_service="api",
        requesting_user_id=user.id,
        data={"user_id": user.id},
    )
    mock_sendgrid = SendgridFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        sendgrid=SendgridRepository(mock_sendgrid),  # type: ignore
    ).user_is_created()

    # Assert new user email is sent
    assert len(mock_sendgrid.sent_emails) == 1
    assert (
        str(mock_sendgrid.sent_emails[0]["subject"]) == "Welcome to Angie's Job Board!"
    )


@pytest.mark.asyncio
async def test_user_is_deleted(request_scope):
    user = UserFixture(request_scope).create_user()
    mock_algolia = AlgoliaClientFactory._return_mock()
    mock_algolia_users = AlgoliaSearchRepository(AlgoliaIndex.CANDIDATES, mock_algolia)
    usecase = UserUseCase(request_scope, mock_algolia_users)
    usecase.make_user_information_public(user.id)
    assert user.id in mock_algolia.index.local_items

    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_is_deleted",
        source_service="api",
        requesting_user_id=user.id,
        data={"user_id": user.id},
    )
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        search_candidates=AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES, mock_algolia
        ),
    ).user_is_deleted()
    assert user.id not in mock_algolia.index.local_items


@pytest.mark.asyncio
async def test_user_is_updated(request_scope):
    user = UserFixture(request_scope).create_user()
    mock_algolia = AlgoliaClientFactory._return_mock()
    mock_algolia_users = AlgoliaSearchRepository(AlgoliaIndex.CANDIDATES, mock_algolia)
    usecase = UserUseCase(request_scope, mock_algolia_users)
    usecase.make_user_information_public(user.id)
    original_algolia_user = mock_algolia.index.local_items.get(user.id)
    updated_user = UserRepository(request_scope).update_fields(
        user.id, first_name="New First Name"
    )
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_is_updated",
        source_service="api",
        requesting_user_id=user.id,
        data=updated_user.model_dump(mode="json"),
    )
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        search_candidates=AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES, mock_algolia
        ),
    ).user_is_updated()
    updated_algolia_user = mock_algolia.index.local_items.get(user.id)
    assert updated_algolia_user
    assert updated_algolia_user != original_algolia_user
    assert updated_algolia_user["first_name"] == "New First Name"


@pytest.mark.asyncio
async def test_user_views_jobs(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_views_jobs",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndJobs(
            user_id=user.id,
            companies_jobs_and_positions=[
                ("abc", "def", 0),
                ("another", "job", 1),
            ],
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
    ).user_views_jobs()

    # Check that 2 user action records were created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 2
    assert count == 2


@pytest.mark.asyncio
async def test_user_clicks_job(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_clicks_job",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndJob(
            user_id=user.id,
            company_id="abc",
            job_id="def",
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )

    mock_insights = AlgoliaInsightsFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        job_insights=AlgoliaInsightsRepository(AlgoliaIndex.JOBS, mock_insights),
    ).user_clicks_job()

    # Check that 1 user action record was created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 1
    assert count == 1

    # Assert algolia insights event is sent
    assert len(mock_insights.sent_events) == 1


@pytest.mark.asyncio
async def test_user_saves_job(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_saves_job",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndJob(
            user_id=user.id,
            company_id="abc",
            job_id="def",
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )
    mock_insights = AlgoliaInsightsFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        job_insights=AlgoliaInsightsRepository(AlgoliaIndex.JOBS, mock_insights),
    ).user_saves_job()

    # Check that 1 user action record was created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 1
    assert count == 1

    # Assert algolia insights event is sent
    assert len(mock_insights.sent_events) == 1


@pytest.mark.asyncio
async def test_user_views_companies(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_views_companies",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndCompanies(
            user_id=user.id,
            companies_and_positions=[
                ("abc", 0),
                ("another", 1),
            ],
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
    ).user_views_companies()

    # Check that 2 user action records were created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 2
    assert count == 2


@pytest.mark.asyncio
async def test_user_clicks_company(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_clicks_company",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndCompany(
            user_id=user.id,
            company_id="abc",
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )

    mock_insights = AlgoliaInsightsFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        company_insights=AlgoliaInsightsRepository(
            AlgoliaIndex.COMPANIES, mock_insights
        ),
    ).user_clicks_company()

    # Check that 1 user action record was created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 1
    assert count == 1

    # Assert algolia insights event is sent
    assert len(mock_insights.sent_events) == 1


@pytest.mark.asyncio
async def test_user_saves_company(request_scope):
    user = UserFixture(request_scope).create_user()
    message = BaseKafkaMessage(
        topic=KafkaTopic.USERS,
        event_type="user_saves_company",
        source_service="api",
        requesting_user_id=user.id,
        data=UserAndCompany(
            user_id=user.id,
            company_id="abc",
            user_is_anonymous=False,
        ).model_dump(mode="json"),
    )
    mock_insights = AlgoliaInsightsFactory._return_mock()
    await AsynchronousUserEvents(
        message=message,
        request_scope=request_scope,
        company_insights=AlgoliaInsightsRepository(
            AlgoliaIndex.COMPANIES, mock_insights
        ),
    ).user_saves_company()

    # Check that 1 user action record was created
    user_actions, count = UserActionRepository(request_scope).query()
    assert len(user_actions) == 1
    assert count == 1

    # Assert algolia insights event is sent
    assert len(mock_insights.sent_events) == 1
