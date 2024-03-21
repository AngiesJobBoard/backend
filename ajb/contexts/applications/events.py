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


class ApplicantAndCompany(BaseModel):
    company_id: str
    job_id: str
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

    def application_is_created(self, company_id: str, job_id: str, application_id: str):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id,
                job_id=job_id,
                application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_SUBMITTED,
        )
    
    def application_is_updated(self, company_id: str, job_id: str, application_id: str):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id,
                job_id=job_id,
                application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_UPDATED,
        )
    
    def application_is_deleted(self, company_id: str, job_id: str, application_id: str):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id,
                job_id=job_id,
                application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_DELETED,
        )
