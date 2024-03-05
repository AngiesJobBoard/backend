import time
import aiohttp
from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.contexts.companies.asynchronous_events import AsynchronousCompanyEvents
from ajb.vendor.openai.repository import AsyncOpenAIRepository

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


async def company_clicks_on_application(
    message: BaseKafkaMessage
):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_clicks_on_application()


async def company_shortlists_application(
    message: BaseKafkaMessage
):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_shortlists_application()


async def company_rejects_application(
    message: BaseKafkaMessage
):
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        sendgrid,
    ).company_rejects_application()


async def company_uploads_resume(message: BaseKafkaMessage):
    async with aiohttp.ClientSession() as session:
        repo = AsynchronousCompanyEvents(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session)
        )
        await repo.company_uploads_resume()


async def company_calculates_match_score(
    message: BaseKafkaMessage
):
    async with aiohttp.ClientSession() as session:
        repo = AsynchronousCompanyEvents(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session)
        )
        await repo.company_calculates_match_score()


ROUTER = {
    CompanyEvent.COMPANY_IS_CREATED.value: company_is_created,
    CompanyEvent.COMPANY_VIEWS_APPLICATIONS.value: company_views_applications,
    CompanyEvent.COMPANY_CLICKS_ON_APPLICATION.value: company_clicks_on_application,
    CompanyEvent.COMPANY_SHORTLISTS_APPLICATION.value: company_shortlists_application,
    CompanyEvent.COMPANY_REJECTS_APPLICATION.value: company_rejects_application,
    CompanyEvent.COMPANY_UPLOADS_RESUME.value: company_uploads_resume,
    CompanyEvent.COMPANY_CALCULATES_MATCH_SCORE.value: company_calculates_match_score,
}
