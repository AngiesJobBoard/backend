import aiohttp
from ajb.base.events import ApplicationEvent, BaseKafkaMessage
from ajb.contexts.applications.asynchronous_events import AsynchronousApplicationEvents
from ajb.vendor.openai.repository import AsyncOpenAIRepository

from services.vendors import make_request_scope


async def company_uploads_resume(message: BaseKafkaMessage):
    async with aiohttp.ClientSession() as session:
        repo = AsynchronousApplicationEvents(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session),
        )
        await repo.upload_resume()


async def company_calculates_match_score(message: BaseKafkaMessage):
    async with aiohttp.ClientSession() as session:
        repo = AsynchronousApplicationEvents(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session),
        )
        await repo.calculate_match_score()


async def company_extracts_application_filters(message: BaseKafkaMessage):
    repo = AsynchronousApplicationEvents(
        message,
        make_request_scope(message),
    )
    await repo.extract_application_filters()


async def company_answers_job_filter_questions(
        message: BaseKafkaMessage
):
    async with aiohttp.ClientSession() as session:
        repo = AsynchronousApplicationEvents(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session)
        )
        await repo.answer_application_questions()


ROUTER = {
    ApplicationEvent.UPLOAD_RESUME.value: company_uploads_resume,
    ApplicationEvent.CALCULATE_MATCH_SCORE.value: company_calculates_match_score,
    ApplicationEvent.EXTRACT_APPLICATION_FILTERS.value: company_extracts_application_filters,
    ApplicationEvent.ANSWER_JOB_FILTER_QUESTIONS.value: company_answers_job_filter_questions,
}
