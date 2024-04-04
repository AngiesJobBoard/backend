import typing as t
from ajb.base import (
    Collection,
    ParentRepository,
    RepositoryRegistry,
    QueryFilterParams,
    RepoFilterParams,
    Pagination,
)
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Filter, Operator, Join

from .models import (
    CompanyApplicationView,
    CreateApplication,
    Application,
    AdminApplicationView,
    ApplicantAndJob,
)


class ApplicationRepository(ParentRepository[CreateApplication, Application]):
    collection = Collection.APPLICATIONS
    entity_model = Application


class CompanyApplicationRepository(ApplicationRepository):
    def _company_get_application(self, company_id: str, application_id: str):
        original_application = self.get(application_id)
        if original_application.company_id != company_id:
            raise EntityNotFound("Application not found")
        return original_application

    def get_company_view_list(
        self,
        company_id: str,
        query: QueryFilterParams | RepoFilterParams | None = None,
        job_id: str | None = None,
        shortlist_only: bool = False,
        match_score: int | None = None,
        new_only: bool = False,
        resume_text_contains: str | None = None,
        has_required_skill: str | None = None,
    ):
        if isinstance(query, QueryFilterParams):
            repo_filters = query.convert_to_repo_filters()
        else:
            repo_filters = query or RepoFilterParams()
        if company_id:
            repo_filters.filters.append(Filter(field="company_id", value=company_id))
        if job_id:
            repo_filters.filters.append(Filter(field="job_id", value=job_id))
        if match_score:
            repo_filters.filters.append(
                Filter(
                    field="application_match_score",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=match_score,
                )
            )
        if shortlist_only:
            repo_filters.filters.append(
                Filter(
                    field="appplication_is_shortlisted",
                    value=True,
                )
            )
        if new_only:
            repo_filters.filters.append(
                Filter(
                    field="application_quick_status",
                    operator=Operator.IS_NULL,
                    value=None,
                )
            )
        if resume_text_contains:
            repo_filters.filters.append(
                Filter(
                    field="extracted_resume_text",
                    operator=Operator.CONTAINS,
                    value=resume_text_contains,
                )
            )
        if has_required_skill:
            repo_filters.filters.append(
                Filter(
                    field="qualifications.skills",
                    operator=Operator.IN,
                    value=has_required_skill,
                )
            )
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=CompanyApplicationView,
        )

    def get_all_company_applications_from_email(
        self, company_id: str, email: str
    ) -> list[ApplicantAndJob]:
        repo_query = RepoFilterParams(
            pagination=Pagination(page=0, page_size=50),
            filters=[
                Filter(field="company_id", value=company_id),
                Filter(field="email", value=email),
            ],
        )
        res, _ = self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_query,
            return_model=ApplicantAndJob,
        )
        casted_result = t.cast(list[ApplicantAndJob], res)
        return casted_result

    def get_company_view_single(self, application_id: str):
        result = self.get_with_joins(
            id=application_id,
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            return_model=CompanyApplicationView,
        )
        casted_result = t.cast(CompanyApplicationView, result)
        if casted_result.email:
            other_applications = self.get_all_company_applications_from_email(
                casted_result.company_id, casted_result.email
            )
        else:
            other_applications = []
        return CompanyApplicationView(
            **casted_result.model_dump(exclude={"other_applications"}),
            other_applications=other_applications
        )

    def get_admin_application_view(
        self,
        repo_filters: QueryFilterParams | RepoFilterParams | None = None,
    ):
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=AdminApplicationView,
        )


RepositoryRegistry.register(ApplicationRepository)
