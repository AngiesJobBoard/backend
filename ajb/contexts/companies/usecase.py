from typing import cast, Any
import re
from concurrent.futures import ThreadPoolExecutor
from ajb.base import BaseUseCase, Collection, RepoFilterParams, Pagination, RequestScope
from ajb.contexts.companies.recruiters.models import CreateRecruiter, RecruiterRole
from ajb.contexts.users.models import User
from ajb.base.events import (
    SourceServices,
)
from ajb.contexts.billing.validate_usage import (
    BillingValidateUsageUseCase,
    TierFeatures,
)
from ajb.vendor.arango.models import Filter, Operator, Join
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.exceptions import RepositoryNotProvided, FeatureNotAvailableOnTier
from ajb.utils import random_salt

from .models import (
    UserCreateCompany,
    CreateCompany,
    Company,
    CompanyGlobalSearchJobs,
    CompanyGlobalSearchApplications,
    CompanyGlobalSearchResults,
    UpdateCompany,
    CompanyImageUpload,
)
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
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        self.request_scope = request_scope
        self.storage_repo = storage

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
            slug_results = company_repo.get_all(slug=data.slug)
            if slug_results:
                data.slug = None

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

    def _global_search_jobs(
        self, company_id: str, text: str, page: int, page_size: int
    ) -> list[CompanyGlobalSearchJobs]:
        job_repo = self.get_repository(Collection.JOBS)
        res, _ = job_repo.query(
            repo_filters=RepoFilterParams(
                pagination=Pagination(page=page, page_size=page_size),
                filters=[Filter(field="company_id", value=company_id)],
                search_filters=[
                    Filter(
                        field="position_title", operator=Operator.CONTAINS, value=text
                    )
                ],
            )
        )
        return [
            CompanyGlobalSearchJobs(
                **job.model_dump(),
            )
            for job in res
        ]

    def _global_search_applicants(
        self, company_id: str, text: str, page: int, page_size: int
    ) -> list[CompanyGlobalSearchApplications]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        res, _ = application_repo.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection=Collection.JOBS.value,
                    from_collection_join_attr="job_id",
                )
            ],
            repo_filters=RepoFilterParams(
                pagination=Pagination(page=page, page_size=page_size),
                filters=[Filter(field="company_id", value=company_id)],
                search_filters=[
                    Filter(field="name", operator=Operator.CONTAINS, value=text),
                    Filter(field="email", operator=Operator.CONTAINS, value=text),
                    Filter(field="phone", operator=Operator.CONTAINS, value=text),
                ],
            ),
            return_model=CompanyGlobalSearchApplications,
        )
        return cast(list[CompanyGlobalSearchApplications], res)

    def get_company_global_search_results(
        self, company_id: str, text: str, page: int, page_size: int
    ) -> CompanyGlobalSearchResults:
        """Search for jobs or applicants all at once"""
        results: dict[str, Any[list[CompanyGlobalSearchApplications]]] = {}
        with ThreadPoolExecutor() as executor:
            results["jobs"] = executor.submit(
                self._global_search_jobs, company_id, text, page, page_size
            )
            results["applications"] = executor.submit(
                self._global_search_applicants, company_id, text, page, page_size
            )
        return CompanyGlobalSearchResults(
            jobs=results["jobs"].result(), applications=results["applications"].result()
        )

    def _update_job_applications_by_email(self, company_id: str, enabled: bool) -> None:
        # Only if feature is available on current subscription
        try:
            BillingValidateUsageUseCase(
                self.request_scope, company_id
            ).validate_feature_access(TierFeatures.EMAIL_INGRESS)
        except FeatureNotAvailableOnTier:
            return

        email_ingress_repository = self.get_repository(
            Collection.COMPANY_EMAIL_INGRESS_WEBHOOKS
        )
        all_email_ingress = email_ingress_repository.get_all(company_id=company_id)
        for ingress in all_email_ingress:
            email_ingress_repository.update_fields(ingress.id, is_active=enabled)

    def update_company(self, company_id: str, updates: UpdateCompany):
        company_repo = self.get_repository(Collection.COMPANIES)
        if updates.settings is not None:
            original_doc: Company = company_repo.get(company_id)
            if (
                original_doc.settings.enable_all_email_ingress
                != updates.settings.enable_all_email_ingress
            ):
                self._update_job_applications_by_email(
                    company_id, updates.settings.enable_all_email_ingress
                )
        return company_repo.update(company_id, updates, merge=False)

    def _create_profile_picture_path(self, company_id: str, file_type: str) -> str:
        return f"companies/{company_id}/profile_picture-{random_salt()}.{file_type}"

    def update_company_main_image(self, company_id: str, data: CompanyImageUpload):
        if not self.storage_repo:
            raise RepositoryNotProvided("Storage")

        company_repo = self.get_repository(Collection.COMPANIES)
        remote_file_path = self._create_profile_picture_path(company_id, data.file_type)
        main_image_url = self.storage_repo.upload_bytes(
            data.picture_data, data.file_type, remote_file_path, True
        )
        return company_repo.update_fields(company_id, main_image=main_image_url)
