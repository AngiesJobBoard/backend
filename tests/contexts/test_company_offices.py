from ajb.base import QueryFilterParams
from ajb.contexts.companies.offices.repository import OfficeRepository
from ajb.contexts.companies.offices.models import (
    CreateOffice,
    UserUpdateOffice,
    Location,
)

from ajb.fixtures.companies import CompanyFixture


def test_create_office_success(request_scope):
    company = CompanyFixture(request_scope).create_company()
    repo = OfficeRepository(request_scope, company.id)

    # No default office returns none
    no_default = repo.get_default_office()
    assert no_default is None

    # Create first office
    office = repo.create(
        CreateOffice(
            name="Office 1",
            company_id=company.id,
            location=Location(
                address_line_1="123 Main St",
                city="New York",
                state="NY",
                country="US",
                zipcode="10001",
            ),
        )
    )
    assert office.default_job_location is True

    # Add a second office as the default
    office_2 = repo.create(
        CreateOffice(
            name="Office 2",
            company_id=company.id,
            location=Location(
                address_line_1="123 Main St",
                city="New York",
                state="NY",
                country="US",
                zipcode="10001",
            ),
            default_job_location=True,
        )
    )
    assert office_2.default_job_location is True

    first_office = repo.get(office.id)
    assert first_office.default_job_location is False

    # Now update the first office as the default
    updated_office_1 = repo.update(
        office.id, UserUpdateOffice(default_job_location=True)
    )

    assert updated_office_1.default_job_location is True

    second_office = repo.get(office_2.id)
    assert second_office.default_job_location is False

    # Get the default and it should be the first
    default_office = repo.get_default_office()
    assert default_office is not None and default_office.id == office.id


def test_get_all_company_offices(request_scope):
    company = CompanyFixture(request_scope).create_company()
    repo = OfficeRepository(request_scope, company.id)
    office_1 = repo.create(
        CreateOffice(
            name="Office 1",
            company_id=company.id,
            location=Location(
                address_line_1="123 Main St",
                city="New York",
                state="NY",
                country="US",
                zipcode="10001",
            ),
        )
    )
    repo.create(
        CreateOffice(
            name="Office 2",
            company_id=company.id,
            location=Location(
                address_line_1="123 Main St",
                city="New York",
                state="NY",
                country="US",
                zipcode="10001",
            ),
        )
    )

    all_offices, count = repo.get_all_by_company()
    assert count == 2
    assert len(all_offices) == 2

    first_office, count = repo.get_all_by_company(
        QueryFilterParams(filters="name=Office 1")
    )
    assert count == 1
    assert len(first_office) == 1
    assert first_office[0].id == office_1.id
