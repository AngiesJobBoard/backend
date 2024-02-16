from ajb.base import (
    BaseUseCase,
    Collection,
)
from ajb.exceptions import CompanyCreateException
from ajb.contexts.companies.recruiters.models import CreateRecruiter, RecruiterRole
from ajb.contexts.users.models import User
from ajb.base.events import (
    SourceServices,
)

from .models import UserCreateCompany, CreateCompany, Company
from .events import CompanyEventProducer


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
                data.slug = data.name.lower().replace(" ", "-")

            # Check if the company name or slug has been taken
            slug_results = company_repo.query(slug=data.slug)
            name_results = company_repo.query(name=data.name)
            if slug_results[0] or name_results[0]:
                raise CompanyCreateException("Company Name or Slug Taken")

            user: User = self.get_object(Collection.USERS, creating_user_id)
            data.owner_first_and_last_name = user.first_name + " " + user.last_name

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
