from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    CompanyEvent,
)
from ajb.exceptions import RequestScopeWithoutCompanyException

from .models import Company


class CompanyAndJob(BaseModel):
    company_id: str
    job_id: str


class CompanyEventProducer(BaseEventProducer):
    def _company_event(self, data: dict, event: CompanyEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.COMPANIES,
            event_type=event,
        )

    def company_created_event(self, created_company: Company):
        self._company_event(
            data=created_company.model_dump(mode="json"),
            event=CompanyEvent.COMPANY_IS_CREATED,
        )

    def company_creates_job(self, company_id: str, job_id: str):
        data = CompanyAndJob(company_id=company_id, job_id=job_id).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_CREATES_JOB,
        )

    def company_updates_job(self, company_id: str, job_id: str):
        data = CompanyAndJob(company_id=company_id, job_id=job_id).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_UPDATES_JOB,
        )

    def company_deletes_job(self, company_id: str, job_id: str):
        data = CompanyAndJob(company_id=company_id, job_id=job_id).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_DELETES_JOB,
        )
