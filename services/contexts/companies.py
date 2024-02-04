from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.contexts.companies.asynchronous_events import AsynchronousCompanyEvents

from services.vendors import (
    search_companies,
    candidate_insights,
    sendgrid,
    make_request_scope,
)


async def company_is_created(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_is_created()


async def company_is_deleted(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_is_deleted()


async def company_is_updated(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_is_updated()


async def company_views_applications(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_views_applications()


async def company_clicks_on_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_clicks_on_application()


async def company_shortlists_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_shortlists_application()


async def company_rejects_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_rejects_application()


async def company_views_candidates(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_views_candidates()


async def company_clicks_candidate(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_clicks_candidate()


async def company_saves_candidate(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        search_companies,
        candidate_insights,
        sendgrid,
    ).company_saves_candidate()


ROUTER = {
    CompanyEvent.COMPANY_IS_CREATED.value: company_is_created,
    CompanyEvent.COMPANY_IS_DELETED.value: company_is_deleted,
    CompanyEvent.COMPANY_IS_UPDATED.value: company_is_updated,
    CompanyEvent.COMPANY_VIEWS_APPLICATIONS.value: company_views_applications,
    CompanyEvent.COMPANY_CLICKS_ON_APPLICATION.value: company_clicks_on_application,
    CompanyEvent.COMPANY_SHORTLISTS_APPLICATION.value: company_shortlists_application,
    CompanyEvent.COMPANY_REJECTS_APPLICATION.value: company_rejects_application,
    CompanyEvent.COMPANY_VIEWS_CANDIDATES.value: company_views_candidates,
    CompanyEvent.COMPANY_CLICKS_CANDIDATE.value: company_clicks_candidate,
    CompanyEvent.COMPANY_SAVES_CANDIDATE.value: company_saves_candidate,
}
