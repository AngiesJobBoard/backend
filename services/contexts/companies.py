from ajb.base.events import CompanyEvent, BaseKafkaMessage
from services.resolvers.companies import CompanyEventsResolver

from services.vendors import (
    sendgrid,
    make_request_scope,
)


async def company_is_created(message: BaseKafkaMessage):
    await CompanyEventsResolver(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_is_created()


async def company_creates_job(message: BaseKafkaMessage):
    await CompanyEventsResolver(
        message,
        make_request_scope(message),
    ).company_creates_job()


async def company_updates_job(message: BaseKafkaMessage):
    await CompanyEventsResolver(
        message,
        make_request_scope(message),
    ).company_updates_job()


async def company_deletes_job(message: BaseKafkaMessage):
    await CompanyEventsResolver(
        message,
        make_request_scope(message),
    ).company_deletes_job()


ROUTER = {
    CompanyEvent.COMPANY_IS_CREATED.value: company_is_created,
    CompanyEvent.COMPANY_CREATES_JOB.value: company_creates_job,
    CompanyEvent.COMPANY_UPDATES_JOB.value: company_updates_job,
    CompanyEvent.COMPANY_DELETES_JOB.value: company_deletes_job,
}
