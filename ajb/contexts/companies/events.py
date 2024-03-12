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


class ResumeAndApplication(BaseModel):
    company_id: str
    job_id: str
    application_id: str
    resume_id: str


class ApplicationId(BaseModel):
    application_id: str


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

    def company_uploads_resume(self, resume_id: str, application_id: str, job_id: str):
        data = ResumeAndApplication(
            company_id=str(self.request_scope.company_id),
            job_id=job_id,
            application_id=application_id,
            resume_id=resume_id,
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_UPLOADS_RESUME,
        )

    def application_is_submited(self, application_id: str):
        self._company_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=CompanyEvent.COMPANY_CALCULATES_MATCH_SCORE,
        )
        self._company_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=CompanyEvent.COMPANY_EXTRACTS_APPLICATION_FILTERS,
        )
        self._company_event(
            data=ApplicationId(application_id=application_id).model_dump(),
            event=CompanyEvent.COMPANY_ANSWERS_JOB_FILTER_QUESTIONS,
        )
