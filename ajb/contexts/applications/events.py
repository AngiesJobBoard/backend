from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    ApplicationEvent,
)


class ResumeAndApplication(BaseModel):
    company_id: str
    job_id: str
    application_id: str
    resume_id: str | None
    parse_resume: bool


class ApplicantAndCompany(BaseModel):
    company_id: str
    job_id: str
    application_id: str


class IngressEvent(BaseModel):
    company_id: str
    ingress_id: str
    raw_ingress_data_id: str


class ApplicationEventProducer(BaseEventProducer):
    def _application_event(self, data: dict, event: ApplicationEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.APPLICATIONS,
            event_type=event,
        )

    def company_uploads_resume(
        self,
        company_id: str,
        resume_id: str | None,
        application_id: str,
        job_id: str,
        parse_resume: bool,
    ):
        data = ResumeAndApplication(
            company_id=company_id,
            job_id=job_id,
            application_id=application_id,
            resume_id=resume_id,
            parse_resume=parse_resume,
        ).model_dump()
        self._application_event(
            data=data,
            event=ApplicationEvent.UPLOAD_RESUME,
        )

    def application_is_submitted(
        self, company_id: str, job_id: str, application_id: str
    ):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id, job_id=job_id, application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_SUBMITTED,
        )

    def application_is_updated(self, company_id: str, job_id: str, application_id: str):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id, job_id=job_id, application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_UPDATED,
        )

    def application_is_deleted(self, company_id: str, job_id: str, application_id: str):
        self._application_event(
            data=ApplicantAndCompany(
                company_id=company_id, job_id=job_id, application_id=application_id
            ).model_dump(),
            event=ApplicationEvent.APPLICATION_IS_DELETED,
        )

    def ingress_event(self, company_id: str, ingress_id: str, raw_ingress_data_id: str):
        self._application_event(
            data=IngressEvent(
                company_id=company_id,
                ingress_id=ingress_id,
                raw_ingress_data_id=raw_ingress_data_id,
            ).model_dump(),
            event=ApplicationEvent.INGRESS_EVENT,
        )
