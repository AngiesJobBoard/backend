from ajb.base import (
    MultipleChildrenRepository,
    RequestScope,
    Collection,
    RepositoryRegistry,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.base.events import SourceServices
from ajb.vendor.arango.models import Join
from ajb.contexts.users.events import UserEventProducer
from .models import SavedJob, CreateSavedJob, SavedJobsListObject


class UserSavedJobsRepository(MultipleChildrenRepository[CreateSavedJob, SavedJob]):
    collection = Collection.USER_SAVED_JOBS
    entity_model = SavedJob

    def __init__(self, request_scope: RequestScope, user_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.USERS.value,
            parent_id=user_id or request_scope.user_id,
        )

    def create(self, entity: CreateSavedJob) -> SavedJob:  # type: ignore
        response = super().create(entity)
        UserEventProducer(self.request_scope, SourceServices.API).user_saves_job(
            job_id=entity.job_id,
            company_id=entity.company_id,
        )
        return response

    def query_with_jobs(
        self, query: QueryFilterParams | RepoFilterParams | None = None
    ):
        query = query or RepoFilterParams()
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
            repo_filters=query,
            return_model=SavedJobsListObject,
        )


RepositoryRegistry.register(UserSavedJobsRepository)
