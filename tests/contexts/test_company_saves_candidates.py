from ajb.contexts.companies.saved_candidates.repository import (
    CompanySavesCandidateRepository,
)
from ajb.contexts.companies.saved_candidates.models import (
    CreateSavedCandidate,
    AlgoliaCandidateSearch,
    SavedCandidatesListObject,
)

from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture


def test_create_and_query(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    repo = CompanySavesCandidateRepository(request_scope, company.id)
    some_candidate = UserFixture(request_scope).create_user(email="nice@candidate.com")
    repo.create(
        CreateSavedCandidate(
            user_id=some_candidate.id,
        )
    )

    results, count = repo.query_with_candidates()
    assert count == 1
    assert len(results) == 1
    assert isinstance(results[0], SavedCandidatesListObject)
    assert results[0].user_id == some_candidate.id
    assert isinstance(results[0].candidate, AlgoliaCandidateSearch)
