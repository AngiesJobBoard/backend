import typing as t
from abc import ABC, abstractmethod
from warnings import warn
from pydantic import BaseModel

from ajb.base import RequestScope, RepoFilterParams
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.models import (
    RawIngressApplication,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    RawIngressApplicationRepository,
)
from ajb.contexts.applications.models import CreateApplication, Application
from ajb.contexts.companies.jobs.repository import JobRepository, Job
from ajb.vendor.arango.models import Filter

T = t.TypeVar("T", bound=BaseModel)


class CouldNotInferJobError(Exception):
    def __init__(self, message: str = "No Job ID Found"):
        super().__init__(message)


class BaseIncomingTransformer(ABC, t.Generic[T]):
    entity_model: t.Type[T]

    def __init__(self, request_scope: RequestScope, raw_data: RawIngressApplication):
        self.request_scope = request_scope
        self.raw_data = raw_data
        self.data: T = self.entity_model(**raw_data.data)
        self.job_id: str | None = None

    def _query_for_job(self, repo_filters: RepoFilterParams):
        repo = JobRepository(self.request_scope)
        potential_results, count = repo.query(repo_filters)
        if count == 0:
            raise CouldNotInferJobError("No job found for the given job name")
        if count > 1:
            raise CouldNotInferJobError("Multiple jobs found for the given job name")
        return potential_results[0]

    def get_job_from_name(self, job_name: str) -> Job:
        repo_filters = RepoFilterParams(
            filters=[Filter(field="company_id", value=self.raw_data.company_id)],
            search_filters=[Filter(field="position_title", value=job_name)],
        )
        return self._query_for_job(repo_filters)

    def get_job_from_external_job_id(self, external_job_id: str) -> Job:
        repo_filters = RepoFilterParams(
            filters=[Filter(field="company_id", value=self.raw_data.company_id)],
            search_filters=[
                Filter(field="external_reference_code", value=external_job_id)
            ],
        )
        return self._query_for_job(repo_filters)

    @abstractmethod
    def infer_job_from_raw_data(self) -> None:
        pass

    @abstractmethod
    def transform_to_application_model(self) -> CreateApplication:
        pass

    @abstractmethod
    def create_application(self) -> Application:
        pass

    def update_raw_record(self, application_id: str) -> None:
        RawIngressApplicationRepository(self.request_scope).update_fields(
            self.raw_data.id, application_id=application_id
        )

    def run(self) -> None:
        if self.raw_data.application_id is not None:
            warn("This record has already been processed")
        self.infer_job_from_raw_data()
        application = self.create_application()
        self.update_raw_record(application.id)
