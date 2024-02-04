from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

from ajb.common.models import DataReducedUser
from ajb.base import BaseDataModel, PaginatedResponse
from ajb.contexts.users.models import User


class AdminRoles(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    READ_ONLY = "read_only"


class UserCreateAdminUser(BaseModel):
    email: str
    role: AdminRoles


class CreateAdminUser(UserCreateAdminUser):
    user_id: str


class AdminUser(BaseDataModel, CreateAdminUser): ...


@dataclass
class AdminUserPaginatedResponse(PaginatedResponse[AdminUser]):
    data: list[AdminUser]


class AdminAndUser(AdminUser):
    user: DataReducedUser


@dataclass
class AdminAndUserPaginatedResponse(PaginatedResponse[AdminAndUser]):
    data: list[AdminAndUser]
