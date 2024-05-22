from typing import cast
from ajb.base import BaseUseCase, Collection, QueryFilterParams, RepoFilterParams

from .models import CompanyAPIIngress


class APIIngressUsecase(BaseUseCase):
    def get_ingress_records_with_count(
        self,
        company_id: str,
        job_id: str | None = None,
        query: QueryFilterParams | RepoFilterParams | None = None,
    ):
        ingress_repo = self.get_repository(Collection.COMPANY_API_INGRESS_WEBHOOKS)
        raw_ingress_repo = self.get_repository(Collection.RAW_INGRESS_APPLICATIONS)

        results, count = ingress_repo.query(query, company_id=company_id)
        results = cast(list[CompanyAPIIngress], results)
        for idx, record in enumerate(results):
            count_kwargs = {
                "ingress_id": record.id,
            }
            if job_id:
                count_kwargs["job_id"] = job_id
            results[idx].record_count = raw_ingress_repo.get_count(
                repo_filters=None, **count_kwargs
            )
        return results, count
