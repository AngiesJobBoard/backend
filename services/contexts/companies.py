from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.contexts.companies.asynchronous_events import AsynchronousCompanyEvents

from services.vendors import (
    sendgrid,
    make_request_scope,
)


async def company_is_created(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_is_created()


async def company_views_applications(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_views_applications()


async def company_clicks_on_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_clicks_on_application()


async def company_shortlists_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_shortlists_application()


async def company_rejects_application(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_rejects_application()


async def company_creates_job(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
    ).company_creates_job()


async def company_updates_job(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
    ).company_updates_job()


async def company_deletes_job(message: BaseKafkaMessage):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
    ).company_deletes_job()


ROUTER = {
    CompanyEvent.COMPANY_IS_CREATED.value: company_is_created,
    CompanyEvent.COMPANY_VIEWS_APPLICATIONS.value: company_views_applications,
    CompanyEvent.COMPANY_CLICKS_ON_APPLICATION.value: company_clicks_on_application,
    CompanyEvent.COMPANY_SHORTLISTS_APPLICATION.value: company_shortlists_application,
    CompanyEvent.COMPANY_REJECTS_APPLICATION.value: company_rejects_application,
    CompanyEvent.COMPANY_CREATES_JOB.value: company_creates_job,
    CompanyEvent.COMPANY_UPDATES_JOB.value: company_updates_job,
    CompanyEvent.COMPANY_DELETES_JOB.value: company_deletes_job,
}
