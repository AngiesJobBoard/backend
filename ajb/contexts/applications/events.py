from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    ApplicationEvent,
)

from ajb.exceptions import RequestScopeWithoutCompanyException


class ResumeAndApplication(BaseModel):
    company_id: str
    job_id: str
    application_id: str
    resume_id: str


class ApplicationId(BaseModel):
    application_id: str


class ApplicationEventProducer(BaseEventProducer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request_scope.company_id is None:
            raise RequestScopeWithoutCompanyException

    def _application_event(self, data: dict, event: ApplicationEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.APPLICATIONS,
            event_type=event,
        )

    def company_uploads_resume(self, resume_id: str, application_id: str, job_id: str):
        data = ResumeAndApplication(
            company_id=str(self.request_scope.company_id),
            job_id=job_id,
            application_id=application_id,
            resume_id=resume_id,
        ).model_dump()
        self._application_event(
            data=data,
            event=ApplicationEvent.UPLOAD_RESUME,
        )

    def application_is_submited(self, application_id: str):
        self._application_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=ApplicationEvent.CALCULATE_MATCH_SCORE,
        )
        self._application_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=ApplicationEvent.EXTRACT_APPLICATION_FILTERS,
        )
        self._application_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=ApplicationEvent.ANSWER_JOB_FILTER_QUESTIONS,
        )
