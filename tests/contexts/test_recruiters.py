from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    CreateRecruiter,
)
from ajb.contexts.companies.recruiters.models import RecruiterRole, RecruiterAndUser
from ajb.vendor.arango.models import Filter, Join
from ajb.base import RepoFilterParams

from ajb.fixtures.users import UserFixture
from ajb.fixtures.companies import CompanyFixture


def test_create_recruiter(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    res = repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )
    assert res.role == RecruiterRole.OWNER

    edges, count = repo.query(user_id=user.id)
    assert count == 1
    assert len(edges) == 1
    assert edges[0].role == RecruiterRole.OWNER


def test_get_recruiters_by_company_id(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    repo.query_with_joins(
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
    )


def test_get_single_recruiter(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    created_recruiter = repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    single_recruiter = repo.get_one_with_joins(
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    collection_alias="user",
                    field="email",
                    value=user.email,
                )
            ]
        ),
    )
    single_recruiter_by_id = repo.get_with_joins(
        id=created_recruiter.id,
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
    )

    assert single_recruiter == single_recruiter_by_id


def test_search_recruiters(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    results, count = repo.get_recruiters_by_company(
        company_id=company.id,
    )

    assert count == 1
    assert len(results) == 1
