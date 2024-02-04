from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    CompanyEvent,
)

from ajb.contexts.search.candidates.models import AlgoliaCandidateSearchResults
from ajb.exceptions import RequestScopeWithoutCompanyException

from .models import Company


class RecruiterAndCandidate(BaseModel):
    company_id: str
    candidate_id: str


class RecruiterAndApplication(BaseModel):
    company_id: str
    application_id: str


class RecruiterAndCandidates(BaseModel):
    company_id: str
    candidates_and_positions: list[tuple[str, int]]


class RecruiterAndApplications(BaseModel):
    company_id: str
    applications_and_positions: list[tuple[str, int]]


class CompanyAndJob(BaseModel):
    company_id: str
    job_id: str


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

    def company_delete_event(self, company_id: str):
        self._company_event(
            data={"company_id": company_id},
            event=CompanyEvent.COMPANY_IS_DELETED,
        )

    def company_is_updated(self, updated_company: Company):
        self._company_event(
            data=updated_company.model_dump(mode="json"),
            event=CompanyEvent.COMPANY_IS_UPDATED,
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

    def company_views_candidates(
        self, results: AlgoliaCandidateSearchResults, search_page: int = 0
    ):
        candidates = [res.user_id for res in results.hits]
        data = RecruiterAndCandidates(
            company_id=str(self.request_scope.company_id),
            candidates_and_positions=[
                (candidate, candidates.index(candidate) + search_page)
                for candidate in candidates
            ],
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_VIEWS_CANDIDATES,
        )

    def company_clicks_candidate(self, candidate_id: str):
        data = RecruiterAndCandidate(
            company_id=str(self.request_scope.company_id), candidate_id=candidate_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_CLICKS_CANDIDATE,
        )

    def company_saves_candidate(self, candidate_id: str):
        data = RecruiterAndCandidate(
            company_id=str(self.request_scope.company_id), candidate_id=candidate_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.COMPANY_SAVES_CANDIDATE,
        )

    def job_submission_is_posted(self, job_id: str):
        data = CompanyAndJob(
            company_id=str(self.request_scope.company_id), job_id=job_id
        ).model_dump()
        self._company_event(
            data=data,
            event=CompanyEvent.JOB_SUBMISSION_IS_POSTED,
        )
