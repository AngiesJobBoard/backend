from datetime import datetime

from ajb.base.models import RequestScope
from ajb.contexts.users.models import User
from ajb.contexts.companies.repository import (
    CompanyRepository,
    CreateCompany,
    Company,
)
from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    CreateRecruiter,
)
from ajb.contexts.companies.jobs.models import (
    CreateJob,
    ScheduleType,
    ExperienceLevel,
    JobLocationType,
    Location,
    Job,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.recruiters.models import RecruiterRole
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionPlan,
)
from ajb.contexts.billing.billing_models import (
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
    SUBSCRIPTION_FEATURE_DEFAULTS,
)

from ajb.fixtures.subscriptions import SubscriptionFixture
from ajb.fixtures.users import UserFixture


class CompanyFixture:
    def __init__(self, request_scope: RequestScope):
        self.request_scope = request_scope

    def create_company(self, create_subscription: bool = True) -> Company:
        # Create the company
        company = CompanyRepository(self.request_scope).create(
            CreateCompany(
                name="Test Company",
                slug="test",
                created_by_user="test",
                owner_email="test@email.com",
            ),
            overridden_id="test",
        )

        # Register a subscription for the company
        if create_subscription:
            SubscriptionFixture().setup_company_subscription(
                self.request_scope, company.id
            )

        return company

    def create_company_with_owner(self) -> tuple[User, Company]:
        user = UserFixture(self.request_scope).create_user()
        company = self.create_company()
        RecruiterRepository(self.request_scope, company.id).create(
            CreateRecruiter(
                company_id=company.id,
                user_id=user.id,
                role=RecruiterRole.OWNER,
            )
        )

        return user, company

    def create_company_job(self, company_id: str) -> Job:
        repo = JobRepository(self.request_scope, company_id)
        return repo.create(
            CreateJob(
                company_id=company_id,
                position_title="Software Engineer",
                description="This is a description",
                industry_category="Software Engineering",
                industry_subcategories=["python"],
                schedule=ScheduleType.FULL_TIME,
                experience_required=ExperienceLevel.eleven_or_more_years,
                location_type=JobLocationType.REMOTE,
                location_override=Location(
                    address_line_1="100 state st",
                    city="Boston",
                    state="MA",
                    country="USA",
                    zipcode="02109",
                    lat=42.35843,
                    lng=-71.05977,
                ),
                required_job_skills=["Python", "Another Fancy Skill"],
                on_job_training_offered=True,
                language_requirements=["English"],
                felons_accepted=False,
                disability_accepted=True,
            )
        )

    def create_partial_job(self, company_id: str):
        repo = JobRepository(self.request_scope, company_id)
        return repo.create(
            CreateJob(
                company_id=company_id,
                position_title="Software Engineer",
            )
        )

    def create_company_subscription(self, company_id: str, plan: SubscriptionPlan):
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company_id
        )
        return subscription_repo.create(
            CreateCompanySubscription.create_trial_subscription(
                company_id, "need to add real usage ID here later..."
            )
        )
