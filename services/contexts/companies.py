import time
from ajb.base.events import CompanyEvent, BaseKafkaMessage
from ajb.contexts.companies.asynchronous_events import AsynchronousCompanyEvents

from services.vendors import (
    sendgrid,
    openai,
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
    print("Starting to scan resume")
    start = time.time()
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        openai=openai
    ).company_uploads_resume()
    print(f"Time to scan resume: {time.time() - start}")


async def company_calculates_match_score(
    message: BaseKafkaMessage
):
    print("Starting match score")
    start = time.time()
    await AsynchronousCompanyEvents(
        message,
        make_request_scope(message),
        openai=openai
    ).company_calculates_match_score()
    print(f"Time to calculate match score: {time.time() - start}")


ROUTER = {
    CompanyEvent.COMPANY_IS_CREATED.value: company_is_created,
    CompanyEvent.COMPANY_VIEWS_APPLICATIONS.value: company_views_applications,
    CompanyEvent.COMPANY_CLICKS_ON_APPLICATION.value: company_clicks_on_application,
    CompanyEvent.COMPANY_SHORTLISTS_APPLICATION.value: company_shortlists_application,
    CompanyEvent.COMPANY_REJECTS_APPLICATION.value: company_rejects_application,
    CompanyEvent.COMPANY_UPLOADS_RESUME.value: company_uploads_resume,
    CompanyEvent.COMPANY_CALCULATES_MATCH_SCORE.value: company_calculates_match_score,
}
