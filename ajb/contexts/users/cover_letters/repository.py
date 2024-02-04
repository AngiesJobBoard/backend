from ajb.base import (
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
    Collection,
)

from .models import CoverLetter, CreateCoverLetter


class CoverLetterRepository(MultipleChildrenRepository[CreateCoverLetter, CoverLetter]):
    collection = Collection.COVER_LETTERS
    entity_model = CoverLetter

    def __init__(self, request_scope: RequestScope, user_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.USERS.value,
            parent_id=user_id or request_scope.user_id,
        )


RepositoryRegistry.register(CoverLetterRepository)
