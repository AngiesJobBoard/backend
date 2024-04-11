from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RequestScope,
    RepositoryRegistry,
)

from .models import (
    CreateApplicationUpdate,
    ApplicationUpdate,
)


class RecruiterUpdatesRepository(
    MultipleChildrenRepository[CreateApplicationUpdate, ApplicationUpdate]
):
    collection = Collection.APPLICATION_RECRUITER_UPDATES
    entity_model = ApplicationUpdate

    def __init__(self, request_scope: RequestScope, application_id: str | None = None):
        super().__init__(request_scope, Collection.APPLICATIONS, application_id)


RepositoryRegistry.register(RecruiterUpdatesRepository)
