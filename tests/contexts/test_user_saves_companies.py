from ajb.contexts.users.saved_companies.repository import (
    UserSavedCompaniesRepository,
)
from ajb.contexts.users.saved_companies.models import (
    CreateSavedCompany,
    SavedCompaniesListObject,
)

from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture


def test_user_saves_companies(request_scope):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    company = CompanyFixture(request_scope).create_company()
    repo = UserSavedCompaniesRepository(request_scope)

    repo.create(CreateSavedCompany(company_id=company.id))
    results, count = repo.query_with_companies()
    assert count == 1
    assert len(results) == 1
    assert isinstance(results[0], SavedCompaniesListObject)
    assert results[0].company.id == company.id
