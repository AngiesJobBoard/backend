from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    CompanyEvent,
)


class CompanyAndJob(BaseModel):
    company_id: str
    job_id: str


class AdminEventProducer(BaseEventProducer):
    def _admin_company_event(self, data: dict, event: CompanyEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.COMPANIES,
            event_type=event,
        )

    def admin_rejects_job_submission(self, company_id: str, job_id: str):
        data = CompanyAndJob(company_id=company_id, job_id=job_id).model_dump()
        self._admin_company_event(
            data=data,
            event=CompanyEvent.ADMIN_REJECTS_JOB_SUBMISSION,
        )
