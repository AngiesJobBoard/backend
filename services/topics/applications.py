import aiohttp
from ajb.base.events import ApplicationEvent, BaseKafkaMessage
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from services.resolvers.applications import ApplicationEventsResolver

from services.vendors import make_request_scope, mixpanel


async def company_uploads_resume(message: BaseKafkaMessage):
    async with aiohttp.ClientSession() as session:
        repo = ApplicationEventsResolver(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session),
        )
        await repo.upload_resume()
    mixpanel.resume_is_scanned(
        message.requesting_user_id,
        message.data["company_id"],
        message.data["application_id"],
    )


async def application_is_submitted(message: BaseKafkaMessage):
    async with aiohttp.ClientSession() as session:
        repo = ApplicationEventsResolver(
            message,
            make_request_scope(message),
            async_openai=AsyncOpenAIRepository(session, model_override="gpt-4-turbo"),
        )
        await repo.application_is_submitted()
    mixpanel.application_is_submitted_and_enriched(
        message.requesting_user_id,
        message.data["company_id"],
        message.data["job_id"],
        message.data["application_id"],
    )


async def application_is_updated(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.application_is_updated()


async def application_is_deleted(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.application_is_deleted()


ROUTER = {
    ApplicationEvent.UPLOAD_RESUME.value: company_uploads_resume,
    ApplicationEvent.APPLICATION_IS_SUBMITTED.value: application_is_submitted,
    ApplicationEvent.APPLICATION_IS_UPDATED.value: application_is_updated,
    ApplicationEvent.APPLICATION_IS_DELETED.value: application_is_deleted,
}
