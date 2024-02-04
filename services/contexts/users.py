from ajb.base.events import UserEvent, BaseKafkaMessage
from ajb.contexts.users.asynchronous_events import AsynchronousUserEvents

from services.vendors import (
    search_candidates,
    job_insights,
    company_insights,
    openai,
    sendgrid,
    make_request_scope,
)


async def user_is_created(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_is_created()


async def user_is_deleted(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_is_deleted()


async def user_is_updated(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_is_updated()


async def user_views_jobs(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_views_jobs()


async def user_clicks_job(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_clicks_job()


async def user_saves_job(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_saves_job()


async def user_applies_to_job(message: BaseKafkaMessage) -> None:
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_applies_to_job()


async def user_views_companies(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_views_companies()


async def user_clicks_company(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_clicks_company()


async def user_saves_company(message: BaseKafkaMessage):
    await AsynchronousUserEvents(
        message,
        make_request_scope(message),
        search_candidates,
        job_insights,
        company_insights,
        openai,
        sendgrid,
    ).user_saves_company()


ROUTER = {
    UserEvent.USER_IS_CREATED.value: user_is_created,
    UserEvent.USER_IS_UPDATED.value: user_is_updated,
    UserEvent.USER_IS_DELETED.value: user_is_deleted,
    UserEvent.USER_VIEWS_JOBS.value: user_views_jobs,
    UserEvent.USER_CLICKS_JOB.value: user_clicks_job,
    UserEvent.USER_SAVES_JOB.value: user_saves_job,
    UserEvent.USER_APPLIES_JOB.value: user_applies_to_job,
    UserEvent.USER_VIEWS_COMPANIES.value: user_views_companies,
    UserEvent.USER_CLICKS_COMPANY.value: user_clicks_company,
    UserEvent.USER_SAVES_COMPANY.value: user_saves_company,
}
