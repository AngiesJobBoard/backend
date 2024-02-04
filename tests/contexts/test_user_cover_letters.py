import typing as t

from ajb.base import Collection
from ajb.contexts.users.cover_letters.repository import (
    CreateCoverLetter,
    CoverLetterRepository,
)


from ajb.fixtures.users import UserFixture


def test_user_cover_letters(request_scope):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    repo = CoverLetterRepository(request_scope)

    # Create
    create_res = repo.create(
        data=CreateCoverLetter(
            cover_letter="Test Cover Letter",
        )
    )

    # Get
    repo.get(id=create_res.id)

    # Internal get to check for parent ID
    internal_get = t.cast(dict, repo.db_collection.get(create_res.id))
    assert Collection.USERS.value in internal_get
    assert internal_get[Collection.USERS.value] == user.id

    # Update
    repo.update(
        id=create_res.id,
        data=CreateCoverLetter(
            cover_letter="Test Cover Letter 2",
        ),
    )

    # Delete
    repo.delete(id=create_res.id)
