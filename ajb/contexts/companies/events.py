from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    CompanyEvent,
)

from ajb.exceptions import RequestScopeWithoutCompanyException

from .models import Company


class RecruiterAndApplication(BaseModel):
    company_id: str
    application_id: str


class RecruiterAndApplications(BaseModel):
    company_id: str
    applications_and_positions: list[tuple[str, int]]


class CompanyEventProducer(BaseEventProducer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request_scope.company_id is None:
            raise RequestScopeWithoutCompanyException

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

    def company_views_applications(
        self, application_ids: list[str], search_page: int = 0
    ):
        data = RecruiterAndApplications(
            company_id=str(self.request_scope.company_id),
            applications_and_positions=[
                (application, application_ids.index(application) + search_page)
                for application in application_ids
            ],
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_VIEWS_APPLICATIONS,
        )

    def company_clicks_on_application(self, application_id: str):
        data = RecruiterAndApplication(
            company_id=str(self.request_scope.company_id), application_id=application_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_CLICKS_ON_APPLICATION,
        )

    def company_shortlists_application(self, application_id: str):
        data = RecruiterAndApplication(
            company_id=str(self.request_scope.company_id), application_id=application_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_SHORTLISTS_APPLICATION,
        )

    def company_rejects_application(self, application_id: str):
        data = RecruiterAndApplication(
            company_id=str(self.request_scope.company_id), application_id=application_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_REJECTS_APPLICATION,
        )
