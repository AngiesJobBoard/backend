from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    UserEvent,
)
from ajb.contexts.search.jobs.models import AlgoliaJobSearchResults
from ajb.contexts.search.companies.models import AlgoliaCompanySearchResults

from .models import User


class UserAndJob(BaseModel):
    user_id: str
    company_id: str
    job_id: str
    user_is_anonymous: bool


class UserJobAndApplication(UserAndJob):
    application_id: str
    resume_id: str


class UserAndJobs(BaseModel):
    user_id: str
    companies_jobs_and_positions: list[tuple[str, str, int]]
    user_is_anonymous: bool


class UserAndCompany(BaseModel):
    user_id: str
    company_id: str
    user_is_anonymous: bool


class UserAndCompanies(BaseModel):
    user_id: str
    companies_and_positions: list[tuple[str, int]]
    user_is_anonymous: bool


class UserEventProducer(BaseEventProducer):
    def _user_event(self, data: dict, event: UserEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.USERS,
            event_type=event,
        )

    def user_created_event(self, created_user: User):
        self._user_event(
            data=created_user.model_dump(mode="json"),
            event=UserEvent.USER_IS_CREATED,
        )

    def user_delete_event(self, user_id: str):
        self._user_event(
            data={"user_id": user_id},
            event=UserEvent.USER_IS_DELETED,
        )

    def user_is_updated(self, updated_user: User):
        self._user_event(
            data=updated_user.model_dump(mode="json"),
            event=UserEvent.USER_IS_UPDATED,
        )

    def user_views_jobs(self, results: AlgoliaJobSearchResults, search_page: int = 0):
        data = UserAndJobs(
            user_id=self.request_scope.user_id,
            companies_jobs_and_positions=[
                (res.company_id, res.job_id, idx + search_page)
                for idx, res in enumerate(results.hits)
            ],
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_VIEWS_JOBS,
        )

    def user_clicks_job(self, company_id: str, job_id: str):
        data = UserAndJob(
            user_id=self.request_scope.user_id,
            company_id=company_id,
            job_id=job_id,
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_CLICKS_JOB,
        )

    def user_saves_job(self, company_id: str, job_id: str):
        data = UserAndJob(
            user_id=self.request_scope.user_id,
            company_id=company_id,
            job_id=job_id,
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_SAVES_JOB,
        )

    def user_applies_job(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        resume_id: str,
    ):
        data = UserJobAndApplication(
            user_id=self.request_scope.user_id,
            company_id=company_id,
            job_id=job_id,
            application_id=application_id,
            resume_id=resume_id,
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_APPLIES_JOB,
        )

    def user_views_companies(
        self, results: AlgoliaCompanySearchResults, search_page: int = 0
    ):
        companies = [res.id for res in results.hits]
        data = UserAndCompanies(
            user_id=self.request_scope.user_id,
            companies_and_positions=[
                (company, companies.index(company) + search_page)
                for company in companies
            ],
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_VIEWS_COMPANIES,
        )

    def user_clicks_company(self, company_id: str):
        data = UserAndCompany(
            user_id=self.request_scope.user_id,
            company_id=company_id,
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_CLICKS_COMPANY,
        )

    def user_saves_company(self, company_id: str):
        data = UserAndCompany(
            user_id=self.request_scope.user_id,
            company_id=company_id,
            user_is_anonymous=self.request_scope.user_is_anonymous,
        ).model_dump()
        self._user_event(
            data=data,
            event=UserEvent.USER_SAVES_COMPANY,
        )
