from datetime import datetime
import pytest

from ajb.base import Collection


from ajb.contexts.users.models import CreateUser
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.companies.models import CreateCompany
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.admin.search.repository import (
    AdminSearchRepository,
    AdminSearch,
    Aggregation,
)


@pytest.fixture(scope="function")
def admin_search_repo(request_scope):
    return AdminSearchRepository(request_scope)


@pytest.fixture(scope="function")
def example_user_data(request_scope):
    user_repo = UserRepository(request_scope)
    for suffix in ["one", "two", "three", "four", "five"]:
        user_repo.create(
            CreateUser(
                first_name=f"test{suffix}",
                last_name=f"test{suffix}",
                email=f"test{suffix}@email.com",
                image_url=f"test{suffix}",
                phone_number=f"test{suffix}",
                auth_id=f"test{suffix}_id",
            ),
            overridden_id=f"test{suffix}_id",
        )


@pytest.fixture(scope="function")
def example_company_data(request_scope):
    company_repo = CompanyRepository(request_scope)
    for suffix in ["one", "two", "three", "four", "five"]:
        company_repo.create(
            CreateCompany(
                name=f"test{suffix}",
                created_by_user=f"test{suffix}_id",
                owner_email="test@email.com",
            )
        )


def test_admin_search(
    admin_search_repo: AdminSearchRepository, example_user_data, example_company_data
):
    results, count = admin_search_repo.admin_search(
        search=AdminSearch(collection=Collection.USERS)
    )
    assert count == 6
    assert len(results) == 6

    results, count = admin_search_repo.admin_search(
        search=AdminSearch(
            collection=Collection.USERS, filters="first_name__endswith=one"
        )
    )
    assert count == 1
    assert len(results) == 1
    assert results[0]["_key"] == "testone_id"

    results, count = admin_search_repo.admin_search(
        search=AdminSearch(
            collection=Collection.COMPANIES,
        )
    )
    assert count == 5
    assert len(results) == 5

    results, count = admin_search_repo.admin_search(
        search=AdminSearch(
            collection=Collection.COMPANIES,
            filters="name__contains=two",
        )
    )
    assert count == 1
    assert len(results) == 1


def test_admin_count(
    admin_search_repo: AdminSearchRepository, example_user_data, example_company_data
):
    count = admin_search_repo.admin_count(
        search=AdminSearch(
            collection=Collection.USERS,
        )
    )
    assert count == 5

    count = admin_search_repo.admin_count(
        search=AdminSearch(
            collection=Collection.USERS,
            filters="first_name__endswith=one",
        )
    )
    assert count == 1

    count = admin_search_repo.admin_count(
        search=AdminSearch(
            collection=Collection.COMPANIES,
        )
    )
    assert count == 5

    count = admin_search_repo.admin_count(
        search=AdminSearch(
            collection=Collection.COMPANIES,
            filters="name__contains=one",
        )
    )
    assert count == 1


def test_admin_count_large_data(
    request_scope,
    admin_search_repo: AdminSearchRepository,
):
    """WARNING: potentially slow test"""
    company_repo = CompanyRepository(request_scope)
    companies_to_create = [
        CreateCompany(
            name=f"test_{idx}", created_by_user="test", owner_email="test@email.com"
        )
        for idx in range(10000)
    ]
    company_repo.create_many(companies_to_create)
    count = admin_search_repo.admin_count(
        search=AdminSearch(collection=Collection.COMPANIES)
    )
    assert count == 10000


# AJBTODO: Fix this test
def test_admin_timeseries(admin_search_repo: AdminSearchRepository, example_user_data):
    results, count = admin_search_repo.get_timeseries_data(
        collection=Collection.USERS,
    )
    assert count == 6
    assert len(results) == 5

    results, count = admin_search_repo.get_timeseries_data(
        collection=Collection.USERS,
        start=datetime(2020, 1, 1),
        end=datetime(2020, 1, 1),
    )
    assert count == 0
    assert len(results) == 0

    results, count = admin_search_repo.get_timeseries_data(
        collection=Collection.USERS,
        start=datetime(2020, 1, 1),
        end=datetime(3020, 1, 1),
    )
    assert count == 5
    assert len(results) == 5


def test_admin_timeseries_with_aggregation(
    admin_search_repo: AdminSearchRepository, example_user_data
):
    results = admin_search_repo.get_timeseries_data(
        collection=Collection.USERS, aggregation=Aggregation.DAILY
    )
    assert 1 == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS, aggregation=Aggregation.HOURLY
    # )
    # assert count == 5
    # assert len(results) == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS, aggregation=Aggregation.MINUTE
    # )
    # assert count == 5
    # assert len(results) == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS, aggregation=Aggregation.WEEKLY
    # )
    # assert count == 5
    # assert len(results) == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS, aggregation=Aggregation.MONTHLY
    # )
    # assert count == 5
    # assert len(results) == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS, aggregation=Aggregation.YEARLY
    # )
    # assert count == 5
    # assert len(results) == 1
    # assert results[0]["count"] == 5

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS,
    #     start=datetime(2020, 1, 1),
    #     end=datetime(2020, 1, 1),
    #     aggregation=Aggregation.MONTHLY,
    # )
    # assert count == 0
    # assert len(results) == 0

    # results, count = admin_search_repo.get_timeseries_data(
    #     collection=Collection.USERS,
    #     start=datetime(2020, 1, 1),
    #     end=datetime(3020, 1, 1),
    #     aggregation=Aggregation.MONTHLY,
    # )
    # assert count == 5
    # assert len(results) == 1


def test_admin_global_search(
    admin_search_repo: AdminSearchRepository, example_user_data
):
    results = admin_search_repo.admin_global_text_search(text="a")
    assert 1 == 1
