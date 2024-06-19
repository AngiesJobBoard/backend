from ajb.base import MultipleChildrenRepository, RepositoryRegistry, Collection, RequestScope

from .models import CreatePublicApplicationForm, PublicApplicationForm


class JobPublicApplicationFormRepository(MultipleChildrenRepository[CreatePublicApplicationForm, PublicApplicationForm]):
    collection = Collection.PUBLIC_APPLICATION_FORMS
    entity_model = PublicApplicationForm

    def __init__(self, request_scope: RequestScope, job_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.JOBS.value,
            parent_id=job_id,
        )


RepositoryRegistry.register(JobPublicApplicationFormRepository)
