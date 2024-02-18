from datetime import datetime
from pydantic import BaseModel
from ajb.base.models import RequestScope
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.models import (
    UserCreatedApplication,
    Application,
    Qualifications,
    WorkHistory,
    Education,
    ContactInformation
)
from ajb.contexts.users.models import User
from ajb.contexts.resumes.models import Resume
from ajb.contexts.companies.models import Company
from ajb.contexts.companies.jobs.models import Job
from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture


class ApplicationData(BaseModel):
    application: Application
    admin: User
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
        resume = user_fixture.create_resume_for_user()

        application_repo = ApplicationRepository(self.request_scope)

        application = application_repo.create(
            UserCreatedApplication(
                company_id=company.id,
                job_id=job.id,
                resume_id=resume.id,
                cover_letter_content="Nice Cover Letter",
                contact_information=ContactInformation(
                    email="nice@email.com",
                    name="Nice Name",
                    phone="123-456-7890",
                ),
                qualifications=Qualifications(
                    most_recent_job=WorkHistory(
                        job_title="Software Engineer",
                        company_name="Test Company",
                        job_industry="Tech",
                        still_at_job=True,
                        start_date=datetime(2023, 1, 1),
                    ),
                    work_history=[
                        WorkHistory(
                            job_title="Software Intern",
                            company_name="Test Company",
                            job_industry="Tech",
                            still_at_job=False,
                            start_date=datetime(2022, 1, 1),
                            end_date=datetime(2023, 1, 1),
                        )
                    ],
                    education=[
                        Education(
                            school_name="Test University",
                            level_of_education="Bachelor's",
                            field_of_study="Computer Science",
                            still_in_school=False,
                            start_date=datetime(2019, 1, 1),
                            end_date=datetime(2023, 1, 1),
                        )
                    ],
                    skills=["Python", "Django", "React"],
                    licenses=["Driver's License"],
                    certifications=["AWS Certified"],
                    language_proficiencies=["English", "Spanish"],
                ),
            )
        )

        return ApplicationData(
            application=application,
            admin=admin,
            resume=resume,
            company=company,
            job=job,
        )
