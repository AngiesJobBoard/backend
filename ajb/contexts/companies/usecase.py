import re
from concurrent.futures import ThreadPoolExecutor
from ajb.base import (
    BaseUseCase,
    Collection,
    build_and_execute_query,
    RepoFilterParams,
    Pagination,
)
from ajb.exceptions import CompanyCreateException
from ajb.contexts.companies.recruiters.models import CreateRecruiter, RecruiterRole
from ajb.contexts.users.models import User
from ajb.base.events import (
    SourceServices,
)
from ajb.vendor.arango.models import Filter, Operator

from .models import UserCreateCompany, CreateCompany, Company
from .events import CompanyEventProducer


def make_arango_safe_key(slug: str) -> str:
    slug = re.sub("[^a-zA-Z0-9-]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        raise ValueError(
            "The processed slug is empty. Provide a non-empty input string."
        )
    return slug.lower()


class CompaniesUseCase(BaseUseCase):
    def user_create_company(
        self, data: UserCreateCompany, creating_user_id: str
    ) -> Company:
        with self.request_scope.start_transaction(
            read_collections=[Collection.COMPANIES],
            write_collections=[Collection.COMPANIES, Collection.COMPANY_RECRUITERS],
        ) as transaction_scope:
            company_repo = self.get_repository(Collection.COMPANIES, transaction_scope)

            # If no slug provided, convert company name to slug and try to create
            slug_provided = data.slug is not None
            if not slug_provided:
                data.slug = make_arango_safe_key(data.name)

            # Check if the company name or slug has been taken
            slug_results = company_repo.query(slug=data.slug)
            if slug_results[0]:
                raise CompanyCreateException("Company Name or Slug Taken")

            user: User = self.get_object(Collection.USERS, creating_user_id)

            # Create the company
            created_company: Company = company_repo.create(
                CreateCompany(
                    **data.model_dump(),
                    created_by_user=creating_user_id,
                    owner_email=user.email,
                ),
                overridden_id=data.slug or None,
            )

            # Add created company to request scope
            self.request_scope.company_id = created_company.id

            # Set creating user as an owner
            self.get_repository(
                Collection.COMPANY_RECRUITERS, transaction_scope, created_company.id
            ).create(
                CreateRecruiter(
                    company_id=created_company.id,
                    user_id=creating_user_id,
                    role=RecruiterRole.OWNER,
                )
            )

            # Produce company create event
            CompanyEventProducer(
                request_scope=self.request_scope, source_service=SourceServices.API
            ).company_created_event(created_company)
        return created_company

    def get_companies_by_user(self, user_id) -> list[Company]:
        company_repo = self.get_repository(Collection.COMPANIES)
        recruiter_records, _ = self.get_repository(Collection.COMPANY_RECRUITERS).query(
            user_id=user_id
        )
        return company_repo.get_many_by_id([record.company_id for record in recruiter_records])  # type: ignore

    def get_company_global_search_results(
        self, company_id: str, text: str, page: int, page_size: int
    ):
        """Search for jobs, applicants, or recruiters all at once"""
        pagination = Pagination(page=page, page_size=page_size)
        jobs_filters = RepoFilterParams(
            filters=[
                Filter(
                    field="company_id",
                    value=company_id,
                ),
            ],
            search_filters=[
                Filter(field="position_title", operator=Operator.CONTAINS, value=text),
            ],
            pagination=pagination,
        )
        application_filters = RepoFilterParams(
            filters=[
                Filter(
                    field="company_id",
                    value=company_id,
                    and_or_operator="AND",
                ),
            ],
            search_filters=[
                Filter(field="name", operator=Operator.CONTAINS, value=text),
                Filter(field="email", operator=Operator.CONTAINS, value=text),
                Filter(field="phone", operator=Operator.CONTAINS, value=text),
            ],
            pagination=pagination,
        )

        results = {}
        with ThreadPoolExecutor() as executor:
            results[Collection.JOBS] = executor.submit(
                build_and_execute_query,
                db=self.request_scope.db,
                collection_name=Collection.JOBS.value,
                repo_filters=jobs_filters,
                execute_type="execute",
                return_fields=["position_title", "_key", "created_at", "total_applicants"],
            )
            results[Collection.APPLICATIONS] = executor.submit(
                build_and_execute_query,
                db=self.request_scope.db,
                collection_name=Collection.APPLICATIONS.value,
                repo_filters=application_filters,
                execute_type="execute",
                return_fields=["_key", "name", "email", "phone", "created_at"],
            )
        return {
            collection: result.result()[0] for collection, result in results.items()
        }
