from ajb.base import BaseUseCase
from ajb.contexts.applications.models import CreateApplication

from .create_many_applications import CreateManyApplicationsResolver


class CreateManyApplicationsFromCSVResolver(BaseUseCase):
    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        partial_candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        return CreateManyApplicationsResolver(
            self.request_scope
        ).create_many_applications(company_id, job_id, partial_candidates)
