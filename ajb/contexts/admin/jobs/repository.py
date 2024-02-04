from ajb.base import (
    ParentRepository,
    RepositoryRegistry,
    Collection,
)
from ajb.vendor.arango.models import Join
from ajb.contexts.companies.jobs.models import AdminSearchJobsWithCompany
from ajb.vendor.arango.models import Filter

from .models import (
    AdminJobPostApproval,
    CreateAdminJobPostApproval,
    DataReducedAdminJobPostApproval,
    JobApprovalStatus,
)


class AdminJobApprovalRepository(
    ParentRepository[CreateAdminJobPostApproval, AdminJobPostApproval]
):
    collection = Collection.ADMIN_JOB_APPROVALS
    entity_model = AdminJobPostApproval

    def query_with_jobs(
        self,
        query: AdminSearchJobsWithCompany = AdminSearchJobsWithCompany(),
        current_status: JobApprovalStatus | None = None,
    ):
        repo_filters = query.convert_to_repo_params()
        if current_status:
            repo_filters.filters.append(
                Filter(
                    field="current_approval_status",
                    value=current_status.value,
                )
            )
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
            return_model=DataReducedAdminJobPostApproval,
        )

    def get_with_job(self, submission_id: str):
        return self.get_with_joins(
            id=submission_id,
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
            return_model=AdminJobPostApproval,
        )


RepositoryRegistry.register(AdminJobApprovalRepository)
