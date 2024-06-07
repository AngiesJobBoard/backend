from ajb.base.events import ApplicationEvent, BaseKafkaMessage
from services.resolvers.applications import ApplicationEventsResolver

from services.vendors import make_request_scope


async def company_uploads_resume(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.upload_resume()


async def company_gets_match_score(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.company_gets_match_score()


async def post_application_submission(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.post_application_submission()


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


async def handle_ingress_event(message: BaseKafkaMessage):
    repo = ApplicationEventsResolver(
        message,
        make_request_scope(message),
    )
    await repo.handle_ingress_event()


ROUTER = {
    ApplicationEvent.UPLOAD_RESUME.value: company_uploads_resume,
    ApplicationEvent.GET_MATCH_SCORE.value: company_gets_match_score,
    ApplicationEvent.POST_APPLICATION_SUBMISSION.value: post_application_submission,
    ApplicationEvent.APPLICATION_IS_UPDATED.value: application_is_updated,
    ApplicationEvent.APPLICATION_IS_DELETED.value: application_is_deleted,
    ApplicationEvent.INGRESS_EVENT.value: handle_ingress_event,
}
