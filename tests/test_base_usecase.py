import pytest

from ajb.base import BaseUseCase, Collection, RepositoryRegistry
from ajb.contexts.companies.models import CreateCompany
from ajb.contexts.companies.repository import CompanyRepository


class ExampleUseCase(BaseUseCase):
    def run_example_action(self, new_company: CreateCompany) -> bool:
        with self.request_scope.start_transaction(
            read_collections=[Collection.COMPANIES],
            write_collections=[Collection.COMPANIES],
        ) as transaction_scope:
            company_repo = self.get_repository(Collection.COMPANIES, transaction_scope)
            company_repo.create(new_company)
            return True

    def run_bad_action(self, new_company: CreateCompany) -> bool:
        with self.request_scope.start_transaction(
            read_collections=[Collection.COMPANIES],
            write_collections=[Collection.COMPANIES],
        ) as transaction_scope:
            company_repo = self.get_repository(Collection.COMPANIES, transaction_scope)
            company_repo.create(new_company)
            raise ValueError("This is a bad action")


def test_example_usecase(request_scope):
    use_case = ExampleUseCase(request_scope)
    assert use_case.run_example_action(
        new_company=CreateCompany(
            name="nice", created_by_user="abc", owner_email="test@email.com"
        )
    )


def test_example_rollback(request_scope):
    # Run the use case and check that no companies exist afterwards
    use_case = ExampleUseCase(request_scope)
    try:
        use_case.run_bad_action(
            new_company=CreateCompany(
                name="nice", created_by_user="abc", owner_email="test@email.com"
            )
        )
    except ValueError:
        pass

    company_repo = CompanyRepository(request_scope)
    assert company_repo.get_count() == 0


def test_get_unregistered_repository_throws_runtime_error():
    with pytest.raises(RuntimeError):
        RepositoryRegistry.get("noexisto")
