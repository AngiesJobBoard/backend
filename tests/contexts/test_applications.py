from ajb.fixtures.applications import ApplicationFixture
from ajb.contexts.applications.repository import CompanyApplicationRepository


def test_company_view_list_basic(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(
        app_data.company.id
    )
    assert len(res) == 1
    assert count == 1

    res, count = repo.get_company_view_list(
        app_data.company.id,
        job_id=app_data.job.id
    )
    assert len(res) == 1
    assert count == 1

def test_company_view_shortlist(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(
        app_data.company.id,
        shortlist_only=True
    )
    assert len(res) == 0
    assert count == 0

    repo.update_fields(
        app_data.application.id,
        appplication_is_shortlisted=True
    )

    res, count = repo.get_company_view_list(
        app_data.company.id,
        shortlist_only=True
    )
    assert len(res) == 1
    assert count == 1


def test_company_view_new_only(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(
        app_data.company.id,
        new_only=True
    )
    assert len(res) == 1
    assert count == 1

    repo.update_fields(
        app_data.application.id,
        viewed_by_company=True
    )

    res, count = repo.get_company_view_list(
        app_data.company.id,
        new_only=True
    )
    assert len(res) == 0
    assert count == 0


def test_match_score_minimum(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    # No match score on this record
    res, count = repo.get_company_view_list(
        app_data.company.id,
        match_score=50
    )
    assert len(res) == 0
    assert count == 0

    # Match updated to a low score
    repo.update_fields(
        app_data.application.id,
        application_match_score=25
    )

    res, count = repo.get_company_view_list(
        app_data.company.id,
        match_score=50
    )
    assert len(res) == 0
    assert count == 0

    # Match score higher now
    repo.update_fields(
        app_data.application.id,
        application_match_score=75
    )   

    res, count = repo.get_company_view_list(
        app_data.company.id,
        match_score=50
    )
    assert len(res) == 1
    assert count == 1


def test_search_applicants_by_resume_text(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    # Update with some fake resume text
    repo.update_fields(
        app_data.application.id,
        extracted_resume_text="I am a software engineer with experience in python"
    )

    # Search for Python
    res, count = repo.get_company_view_list(
        app_data.company.id,
        resume_text_contains="python"
    )
    assert len(res) == 1
    assert count == 1


def test_search_applications_by_skills(request_scope):
    app_data = ApplicationFixture(request_scope).create_application()
    repo = CompanyApplicationRepository(request_scope)

    # Default job fixture comes with [Python, Another Fancy Skill]
    res, _ = repo.get_company_view_list(
        app_data.company.id,
        has_required_skill="Py"
    )
    assert len(res) == 1

    res, _ = repo.get_company_view_list(
        app_data.company.id,
        has_required_skill="nolo existo"
    )
    assert len(res) == 0


# def test_search_applications_by_many(request_scope):
#     app_data = ApplicationFixture(request_scope).create_application()


# def test_application_count(request_scope):
#     app_data = ApplicationFixture(request_scope).create_application()
