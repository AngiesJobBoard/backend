from ajb.base import (
    MultipleChildrenRepository,
    Collection,
    RequestScope,
    RepositoryRegistry,
)
from ajb.base.models import RequestScope

from .models import Resume, CreateResume


class ResumeRepository(MultipleChildrenRepository[CreateResume, Resume]):
    collection = Collection.RESUMES
    entity_model = Resume

    def __init__(self, request_scope: RequestScope, user_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.USERS.value,
            parent_id=user_id or request_scope.user_id,
        )


RepositoryRegistry.register(ResumeRepository)
