from ajb.base import (
    MultipleChildrenRepository,
    Collection,
    RequestScope,
    RepositoryRegistry,
    QueryFilterParams,
)
from ajb.vendor.arango.models import Filter
from ajb.exceptions import EntityNotFound

from .models import CreateOffice, Office, UserUpdateOffice


class OfficeRepository(MultipleChildrenRepository[CreateOffice, Office]):
    collection = Collection.COMPANY_OFFICES
    entity_model = Office

    def __init__(self, request_scope: RequestScope, company_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    def create(self, data: CreateOffice, overridden_id: str | None = None) -> Office:  # type: ignore
        other_offices, _ = self.query()

        # If this is the first office, make it the default
        data.default_job_location = (
            True if not other_offices else data.default_job_location
        )

        # If the office is default, make all other offices not default
        default_office = self.get_default_office()
        if default_office and data.default_job_location:
            self.update_fields(default_office.id, default_job_location=False)

        # Now create it
        return super().create(data, overridden_id)

    def update(self, id: str, data: UserUpdateOffice) -> Office:  # type: ignore
        # If the updated office is the default, set other offices to not default
        if data.default_job_location:
            default_office = self.get_default_office()
            if default_office and default_office.id != id:
                self.update_fields(default_office.id, default_job_location=False)

        # Now update it
        return super().update(id, data)

    def get_all_by_company(self, query: QueryFilterParams = QueryFilterParams()):
        repo_filters = query.convert_to_repo_filters()
        repo_filters.filters.append(Filter(field="company_id", value=self.parent_id))
        return self.query(repo_filters)

    def get_default_office(self) -> Office | None:
        try:
            return self.get_one(default_job_location=True)
        except EntityNotFound:
            return None


RepositoryRegistry.register(OfficeRepository)
