from pydantic import BaseModel
from ajb.base.models import RequestScope
from ajb.contexts.applications.usecase import ApplicationsUseCase
from ajb.contexts.applications.models import UserCreatedApplication, Application
from ajb.contexts.users.models import User
from ajb.contexts.users.resumes.models import Resume
from ajb.contexts.companies.models import Company
from ajb.contexts.companies.jobs.models import Job
from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture


class ApplicationData(BaseModel):
    application: Application
    admin: User
    user: User
    resume: Resume
    company: Company
    job: Job


class ApplicationFixture:
    def __init__(self, request_scope: RequestScope):
        self.request_scope = request_scope

    def create_application(self) -> ApplicationData:
        company_fixture = CompanyFixture(self.request_scope)
        admin, company = company_fixture.create_company_with_owner()
        job = company_fixture.create_company_job(company.id)

        user_fixture = UserFixture(self.request_scope)
        applying_user = user_fixture.create_user(email="apply@email.com")
        resume = user_fixture.create_resume_for_user(applying_user.id)

        usecase = ApplicationsUseCase(self.request_scope)
        application = usecase.user_creates_application(
            applying_user.id,
            UserCreatedApplication(
                company_id=company.id,
                job_id=job.id,
                resume_id=resume.id,
            ),
        )

        return ApplicationData(
            application=application,
            admin=admin,
            user=applying_user,
            resume=resume,
            company=company,
            job=job,
        )
