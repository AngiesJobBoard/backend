from ajb.base import (
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
    Collection,
    RepoFilterParams,
    QueryFilterParams,
)
from ajb.vendor.arango.models import Join, Filter

from .models import (
    Job,
    CreateJob,
    JobWithCompany,
    AdminSearchJobsWithCompany,
)


class JobRepository(MultipleChildrenRepository[CreateJob, Job]):
    collection = Collection.JOBS
    entity_model = Job
    search_fields = ("position_title",)

    def __init__(self, request_scope: RequestScope, company_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    def get_company_jobs(
        self,
        company_id: str,
        query: QueryFilterParams | RepoFilterParams | None = None,
    ) -> tuple[list[Job], int]:
        # Better optimiation in the future is to track the count of applications in the job document directly
        if isinstance(query, QueryFilterParams):
            query = query.convert_to_repo_filters()
        else:
            query = query or RepoFilterParams()
        query.filters.append(Filter(field="company_id", value=company_id))
        results, count = self.query_with_joins(
            joins=[
                Join(
                    to_collection="applications",
                    to_collection_alias="application",
                    to_collection_join_attr="job_id",
                    from_collection_join_attr="_key",
                    is_aggregate=True,
                )
            ],
            repo_filters=query,
        )
        formatted_job_results = [
            Job(
                **job,
                applicants=len(job["application"]) if job.get("application") else 0,
                shortlisted_applicants=len(
                    [
                        application
                        for application in job["application"]
                        if application.get("application_is_shortlisted")
                    ]
                ),
                id=job["_key"],
            )
            for job in results
        ]
        return formatted_job_results, count

    def get_jobs_with_company(
        self,
        job_id: str | None = None,
        query: AdminSearchJobsWithCompany = AdminSearchJobsWithCompany(),
        is_live: bool = False,
        is_boosted: bool = False,
    ) -> tuple[list[JobWithCompany], int]:
        formatted_query = query.convert_to_repo_params()
        if job_id:
            formatted_query.filters.append(Filter(field="_key", value=job_id))
        if is_live:
            formatted_query.filters.append(Filter(field="is_live", value=is_live))
        if is_boosted:
            formatted_query.filters.append(Filter(field="is_boosted", value=is_boosted))
        return self.query_with_joins(  # type: ignore
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                )
            ],
            repo_filters=formatted_query,
            return_model=JobWithCompany,
        )


RepositoryRegistry.register(JobRepository)
