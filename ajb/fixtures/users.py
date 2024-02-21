from ajb.base.models import RequestScope
from ajb.contexts.users.models import CreateUser, User
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.admin.users.repository import AdminUserRepository
from ajb.contexts.admin.users.models import CreateAdminUser, AdminRoles
from ajb.contexts.resumes.models import Resume, CreateResume
from ajb.contexts.resumes.repository import ResumeRepository


class UserFixture:
    def __init__(self, request_scope: RequestScope):
        self.request_scope = request_scope

    def create_user(self, email: str = "test@email.com") -> User:
        return UserRepository(self.request_scope).create(
            CreateUser(
                first_name="Testy",
                last_name="McGee",
                email=email,
                image_url="test",
                phone_number="test",
                auth_id="test_id",
            )
        )

    def create_admin_user(self, email: str = "admin@email.com") -> User:
        created_user = UserRepository(self.request_scope).create(
            CreateUser(
                first_name="admin",
                last_name="mcgee",
                email=email,
                image_url="test",
                phone_number="test",
                auth_id="test_id",
            )
        )
        AdminUserRepository(self.request_scope).create(
            CreateAdminUser(
                email=email, role=AdminRoles.ADMIN, user_id=created_user.id
            ),
            overridden_id=created_user.id,
        )
        return created_user

    def create_resume_for_user(self) -> Resume:
        return ResumeRepository(self.request_scope).create(
            CreateResume(
                remote_file_path="test", resume_url="nice.com", file_name="test", company_id="test", job_id="test"
            )
        )
